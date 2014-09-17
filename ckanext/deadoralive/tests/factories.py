import factory

import ckan.model
import ckan.new_tests.helpers as helpers


# This function is copy-pasted from CKAN's master branch because we need it
# here and it's not on CKAN's release-v2.2 branch which we're working against.
def _get_action_user_name(kwargs):
    '''Return the name of the user in kwargs, defaulting to the site user

    It can be overriden by explictly setting {'user': None} in the keyword
    arguments. In that case, this method will return None.
    '''

    if 'user' in kwargs:
        user = kwargs['user']
    else:
        user = helpers.call_action('get_site_user')

    if user is None:
        user_name = None
    else:
        user_name = user['name']

    return user_name


# This class is copy-pasted from CKAN's master branch because we need it
# here and it's not on CKAN's release-v2.2 branch which we're working against.
class Dataset(factory.Factory):
    '''A factory class for creating CKAN datasets.'''

    FACTORY_FOR = ckan.model.Package

    # These are the default params that will be used to create new groups.
    title = 'Test Dataset'
    description = 'Just another test dataset.'

    # Generate a different group name param for each user that gets created.
    name = factory.Sequence(lambda n: 'test_dataset_{n}'.format(n=n))

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError(".build() isn't supported in CKAN")

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        context = {'user': _get_action_user_name(kwargs)}

        dataset_dict = helpers.call_action('package_create',
                                           context=context,
                                           **kwargs)
        return dataset_dict


# This class is copy-pasted from CKAN's master branch because we need it
# here and it's not on CKAN's release-v2.2 branch which we're working against.
class Resource(factory.Factory):
    '''A factory class for creating CKAN resources.'''

    FACTORY_FOR = ckan.model.Resource

    name = factory.Sequence(lambda n: 'test_resource_{n}'.format(n=n))
    description = 'Just another test resource.'
    format = 'res_format'
    url = 'http://link.to.some.data'
    package_id = factory.LazyAttribute(lambda _: Dataset()['id'])

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError(".build() isn't supported in CKAN")

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        context = {'user': _get_action_user_name(kwargs)}

        resource_dict = helpers.call_action('resource_create', context=context,
                                            **kwargs)
        return resource_dict
