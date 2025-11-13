#!/bin/bash

# purge_css.sh

echo "$(date +'%Y-%m-%dT%H:%M:%S') - $0 - CSS purge and minification..."

# See: https://purgecss.com/CLI.html
# sudo npm i -g purgecss
mkdir -p ./temp_purgecss
find ./_site -type f -name "*.css" \
    -exec echo {} \; \
    -exec purgecss --css {} --content "./_site/**/*.js" "./_site/**/*.html" -o ./temp_purgecss \; \
    -exec bash -c ' mv "./temp_purgecss/`basename {}`" "`dirname {}`" ' \;
rmdir ./temp_purgecss

# See: https://github.com/mishoo/UglifyJS
# sudo npm install uglify-js -g
# minification of JS files
find ./_site -type f \
    -name "*.js" ! -name "*.min.*" ! -name "vfs_fonts*" \
    -exec echo {} \; \
    -exec uglifyjs -o {}.min {} \; \
    -exec rm {} \; \
    -exec mv {}.min {} \;

# sudo npm install uglifycss -g
# minification of CSS files
find ./_site -type f \
    -name "*.css" ! -name "*.min.*" \
    -exec echo {} \; \
    -exec uglifycss --output {}.min {} \; \
    -exec rm {} \; \
    -exec mv {}.min {} \;

echo "$(date +'%Y-%m-%dT%H:%M:%S') - $0 - End."
