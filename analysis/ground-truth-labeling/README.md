
prerequisites:
- `just`
- ImageMagick
- tk `+quartz` variant
- GNU parallel. If you have a version installed on OSX from `moreutils`,
     follow these instructions https://superuser.com/questions/545889/how-can-i-install-gnu-parallel-alongside-moreutils/.

MacPorts:
```
sudo port install just ImageMagick
sudo port install tk +quartz
```

Homebrew:
```
brew install just
brew install ImageMagick
brew install tcl-tk
```

hand labeling and annotating:

1. create symlink to the location of `output-2023-01-18`:
   ```
   just create-symlink /path/to/output-2023-01-18
   ```

2. stitch the images together (make sure your prerequisites are
   installed):
   ```
   just stitch-images
   ```

3. install simplabel:
   ```
   just install-simplabel
   ```

4. start/continue labeling:
   ```
   just label
   ```

5. after saving/quitting, the exported JSON file is located at the
   following path: `working-2023-01-18/labeled_user.json`

   TODO parse this file into a CSV or something

----

labels:
```
1st
amazon
apple
github
google
facebook
linkedin
microsoft
twitter
yahoo
other
meta-recrawl
meta-broken
```
