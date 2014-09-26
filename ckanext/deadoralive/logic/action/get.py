import datetime

import pylons.config

import ckan.plugins.toolkit as toolkit
import ckanext.deadoralive.model.results as results
import ckanext.deadoralive.config as config


def get_resources_to_check(context, data_dict):
    """Return a list of up to ``n`` resource IDs to be checked.

    Returns up to ``n`` resource IDs to be checked for broken links.

    Resources that have not been checked before will be returned first, oldest
    resources first.

    Resources that have not been checked in the last 24 hours (configurable:
    ``ckanext.deadoralive.recheck_resources_after``) will be returned next,
    most-recently-checked resources last.

    As soon as a resource's ID is returned by this function that resource is
    considered to have a "pending" check (we are expecting to receive a link
    check result for that resource soon). Resources with pending checks will
    not be returned by this function again for at least 2 hours (configurable:
    ``ckanext.deadoralive.resend_pending_resources_after``).

    :param n: the maximum number of resources to return at once
    :type n: int

    :rtype: list of strings

    """
    toolkit.check_access("ckanext_deadoralive_get_resources_to_check",
                         context, data_dict)

    # TODO: Validation.

    recheck_resources_after = config.recheck_resources_after
    since_delta = datetime.timedelta(hours=recheck_resources_after)
    resend_pending_resources_after = (
        config.resend_pending_resources_after)
    pending_since_delta = datetime.timedelta(
        hours=resend_pending_resources_after)

    n = data_dict.get("n", 50)

    return results.get_resources_to_check(n, since=since_delta,
                                          pending_since=pending_since_delta)


def _is_broken(result):
    """Return True if the given link checker result represents a broken link.

    This implements our configurable "A link is broken if it has been broken
    for at least N consecutive checks over a period of at least M days" logic
    for deciding whether a link is broken or not.

    """
    if not result:
        return False

    n = config.broken_resource_min_fails
    m = config.broken_resource_min_hours
    m_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=m)

    # Innocent until proven guilty.
    broken = False

    # We won't mark a link as "working" if it has never been checked
    # successfully. It may not pass our test to be marked as broken if it hasn't
    # been checked n times, but we will leave it unmarked rather than mark it
    # as working.
    if not result["last_successful"]:
        broken = None

    # Mark the resource as broken if it has at least n consecutive fails over
    # a period of at least m hours.
    if result["num_fails"] >= n:
        last_successful = result["last_successful"]
        if last_successful is None or last_successful < m_hours_ago:
            broken = True

    return broken


@toolkit.side_effect_free
def get(context, data_dict):
    """Get the latest link check result data for a resource.

    :param resource_id: the resource to return the result data for
    :type resource_id: string

    :returns: the latest link check data for the resource, or None if there are
      no results for this resource
    :rtype: dict or None

    """
    toolkit.check_access("ckanext_deadoralive_get", context, data_dict)

    # TODO: Validation.

    resource_id = data_dict["resource_id"]

    try:
        result = results.get(resource_id)
    except results.NoResultForResourceError:
        return None

    result["broken"] = _is_broken(result)

    return result


def _broken_links_by_organization(context, organization_list, all_results,
                                  package_search):

    # Get a list of the names of all the site's organizations.
    organizations = organization_list(context=context,
                                      data_dict={'all_fields': True})

    # Get a dict mapping resource IDs to link checker results.
    result_dicts = {}
    for result in all_results():
        assert result["resource_id"] not in result_dicts
        result_dicts[result["resource_id"]] = result

    # Build the datasets with broken links by organization report.
    report = []
    for organization in organizations:

        organization_report_item = {
            "name": organization["name"],
            "display_name": (organization.get("title")
                             or organization.get("name")),
            "image_display_url": organization["image_display_url"],
            "description": organization["description"],
            "packages": organization["packages"],
            "datasets_with_broken_links": []}
        num_broken_links = 0

        # Get a list of all the organization's datasets
        # (these are full dataset dicts, including a list of resource dicts
        # for each dataset).
        datasets = package_search(
            data_dict={"fq": "organization:{name}".format(
                name=organization["name"])})

        # Build the report dict for each of the organization's datasets.
        for dataset in datasets:
            resource_ids = [resource["id"] for resource in dataset["resources"]]
            broken_resource_ids = [resource_id for resource_id in resource_ids
                                   if _is_broken(result_dicts.get(resource_id))]
            num_broken_links += len(broken_resource_ids)
            if broken_resource_ids:  # Only report datasets with broken links.
                dataset_report_item = {
                    "name": dataset["name"],
                    "display_name": dataset.get("title") or dataset.get("name"),
                    "num_broken_links": len(broken_resource_ids),
                    "resources_with_broken_links": broken_resource_ids,
                    }
                organization_report_item["datasets_with_broken_links"].append(
                    dataset_report_item)
        organization_report_item["num_broken_links"] = num_broken_links
        organization_report_item["datasets_with_broken_links"].sort(
            key=lambda x: x["num_broken_links"], reverse=True)
        report.append(organization_report_item)

    report.sort(key=lambda x: x["num_broken_links"], reverse=True)

    return report


def _package_search(context=None, data_dict=None):
    """A simple wrapper for CKAN's package_search API action.

    Returns just the "results" part of the response, and not the rest.

    """
    return toolkit.get_action("package_search")(context=context,
                                                data_dict=data_dict)["results"]


@toolkit.side_effect_free
def broken_links_by_organization(context, data_dict):
    """Return a datasets with broken links grouped by organization report.

    Returns a list of all the resources with broken links on the site, grouped
    by dataset, with the datasets grouped by organization, and sorted with
    organizations and datasets with the most broken resources first.

    Sample output::

        [
          { "name": "organization-name",
            "num_broken_links": 999,
            "datasets_with_broken_links": [
              { "name": "dataset name",
                "num_broken_links": 9,
                "resources_with_broken_links": [
                    { "id": 'resource_id", }
                    ...
                ]
              },
              ...
          },
          ...
        ]

    """
    toolkit.check_access("ckanext_deadoralive_broken_links_by_organization",
                         context, data_dict)

    organization_list = toolkit.get_action("organization_list")
    return _broken_links_by_organization(
        context, organization_list, results.all, _package_search)


def _get_email_for_dataset(dataset):
    return dataset.get('maintainer_email') or dataset.get('author_email')


@toolkit.side_effect_free
def broken_links_by_email(context, data_dict):
    """Return a report of datasets with broken links grouped by email.

    Datasets with the same maintainer or author email address are grouped
    together, intended to make it convenient for sysadmins to email the people
    responsible for datasets about broken links.

    Sample output::

        [
          { "email": "someone@someorganization.com",
            "mailto": "<mailto URL for emailing them about their broken links>",
            "num_broken_links": 999,
            "datasets_with_broken_links": [
              { "name": "dataset name",
                "num_broken_links": 9,
                "resources_with_broken_links": [
                    { "id": 'resource_id", }
                    ...
                ]
              },
              ...
          },
          ...
        ]

    """
    toolkit.check_access("ckanext_deadoralive_broken_links_by_email",
                         context, data_dict)

    # Get a dict mapping resource IDs to link checker results.
    result_dicts = {}
    for result in results.all():
        assert result["resource_id"] not in result_dicts
        result_dicts[result["resource_id"]] = result

    # Get a list of all the broken datasets on the site, each with a sub-list of
    # all its broken resources.
    broken_datasets = []
    # FIXME: Does package search always return all the datasets here?
    for dataset in _package_search(data_dict={}):
        broken_resources = []
        for resource in dataset.get('resources'):
            if _is_broken(result_dicts.get(resource["id"])):
                broken_resources.append(resource["id"])
        if broken_resources:
            broken_datasets.append(dict(
                name=dataset["name"], title=dataset["title"],
                num_broken_links=len(broken_resources),
                resources_with_broken_links=broken_resources,
                email=_get_email_for_dataset(dataset)))

    # Group the broken datasets by email.
    # We do this as a dict at first because it's easier.
    emails = {}
    for dataset in broken_datasets:
        email = dataset["email"]
        if email not in emails:
            emails[email] = {"datasets_with_broken_links": [dataset]}
        else:
            emails[email]["datasets_with_broken_links"].append(dataset)

    # Add num. broken links per email, and sort the list of broken datasets for
    # each email.
    for email in emails:
        num_broken_links = 0
        for dataset in emails[email]["datasets_with_broken_links"]:
            num_broken_links += dataset["num_broken_links"]
        emails[email]["num_broken_links"] = num_broken_links
        # Sort the datasets with most broken links first.
        emails[email]["datasets_with_broken_links"].sort(
            key=lambda x: x["num_broken_links"], reverse=True)

    # Turn out dict mapping emails -> broken datasets into a list.
    report = []
    for email, dict_ in emails.items():
        dict_["email"] = email
        report.append(dict_)
    # Sort the emails with the most broken links first.
    report.sort(key=lambda x: x["num_broken_links"], reverse=True)

    # Add mailto: URLs to each report item.
    for item in report:

        if not item["email"]:
            continue

        if len(item["datasets_with_broken_links"]) == 1:
            subject = "You have a dataset with broken links on {site}"
            subject = subject.format(site=pylons.config["ckan.site_title"])
            body = "This dataset contains a broken link:%0A%0A{title}%0A{url}"
            broken_dataset = item["datasets_with_broken_links"][0]
            url = pylons.config["ckan.site_url"] + toolkit.url_for(
                controller="package", action="read", id=broken_dataset["name"])
            body = body.format(title=broken_dataset["title"], url=url)

        else:
            subject = "You have {n} datasets with broken links on {site}"
            subject = subject.format(n=len(item["datasets_with_broken_links"]),
                                     site=pylons.config["ckan.site_title"])
            body = "These datasets have broken links:"
            for dataset in item["datasets_with_broken_links"]:
                url = pylons.config["ckan.site_url"] + toolkit.url_for(
                    controller="package", action="read", id=dataset["name"])
                body += "%0A%0A{title}%0A{url}".format(
                    title=dataset["title"], url=url)

        item["mailto"] = "mailto:{email}?subject={subject}&body={body}".format(
            email=item["email"], subject=subject, body=body)

    return report
