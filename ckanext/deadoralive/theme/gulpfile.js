var gulp = require('gulp');
var less = require('gulp-less');
var compressor = require('gulp-compressor');

var paths = {
  src: {
    less: './assets/less/**/*'
  },
  dest: {
    less: './resources/styles/'
  }
};

gulp.task('less', function() {
  return gulp.src(paths.src.less)
    .pipe(less())
    .pipe(compressor())
    .pipe(gulp.dest(paths.dest.less));
});

gulp.task('watch', function() {
  gulp.watch(paths.src.less, ['less']);
});

gulp.task('default', ['less']);
