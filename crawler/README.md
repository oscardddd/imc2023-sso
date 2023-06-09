# internal-pages-research/client

## quick start (one page)

On macOS with MacPorts:
```
# install dependencies
sudo port install nodejs17 npm8 just parallel
just install-deps
just install-chrome
just install-isdcac

# run clicker.js on grubhub.com
just run-clicker-test
```

The output, stored in the folder `output-DEV`, will be in CSV format
with the following headers:
```
outputPrefix,timestamp,url,login_url,screenshot_url,screenshot_login_url,1st,amazon,apple,github,google,facebook,linkedin,microsoft,twitter,yahoo
```
with an example:
```
9999,2023-06-01T19:14:34.592Z,https://www.grubhub.com,https://www.grubhub.com/login,9999-https!www.grubhub.com-20230601191434593-0.png,9999-https!www.grubhub.com-20230601191434593-1.png,9999-https!www.grubhub.com-20230601191434593-0.html.gz,9999-https!www.grubhub.com-20230601191434593-1.html.gz,1,1,0,0,1,1,0,0,0,0
```

## quick start (crux top 1K)

Now that we've run **Quick Start (One Page)** successfully,
we can now crawl the sites on the Top Lists.

The [CrUX dataset](https://github.com/zakird/crux-top-lists)
contains the Top 1M sites, binned at 1K, 5K, ...:
we'll use only the Top 1K.

With the CrUX Top 1K, we'll parallelize our crawl using our
  `clicker.js` with `parallel`.
The default is 3 parallel jobs with a 2 second delay in between.
If using an ad-blocking DNS resolver (e.g., Pi-Hole, NextDNS),
  it's helpful to configure your system to use a public
  resolver (Google, Cloudflare, your ISP).

The following snippet will take ~3-4 hours to run:
```
# download and extract the CrUX dataset
just download-crux-202304

# run crawler over the Top 1K
just crawl-crux-202304

# coalesce the results
just generate-csv-DEV

# view the results
less websites-DEV.csv
```

The output has the same format as previously described:
```
outputPrefix,timestamp,url,login_url,screenshot_url,screenshot_login_url,1st,amazon,apple,github,google,facebook,linkedin,microsoft,twitter,yahoo
```

In the case of crawling the CrUX lists, the `outputPrefix` contains the
bin that the site is in (e.g., `1000` for Top 1K, `5000` for Top 5K,
etc.).

## manually install dependencies

### install node.js

Install [Node.js](https://nodejs.org/en/) manually or using your
favorite package manager.

On MacPorts (macOS), install using the following:
```shell
$ sudo port install nodejs17 npm8
```

Test that `node` and `npm` are working:
```shell
$ node --version
v17.8.0
$ npm --version
8.5.5
```

### install clicker.js dependencies

The [package.json](./package.json) contains the main dependency,
[Playwright](https://playwright.dev).

In this directory (`internal-pages-research/client`), run the following
command:
```shell
$ npm install
```

The Chromium, Firefox, and WebKit browsers are downloaded as part of the
Playwright installation process. You can also point to a Chrome or
Firefox binary of your choice, too.

We need the official version of Google Chrome (if not already installed):
```shell
$ npx playwright install chrome
```

## clicker.js

**clicker.js** tries to find the login pages and the OAuth providers.

### example

```shell
$ node --unhandled-rejections=strict clicker.js --url https://www.grubhub.com --timetolive 1000
9999,2023-06-01T19:14:34.592Z,https://www.grubhub.com,https://www.grubhub.com/login,9999-https!www.grubhub.com-20230601191434593-0.png,9999-https!www.grubhub.com-20230601191434593-1.png,9999-https!www.grubhub.com-20230601191434593-0.html.gz,9999-https!www.grubhub.com-20230601191434593-1.html.gz,1,1,0,0,1,1,0,0,0,0
```

### usage

```
usage: clicker.js [-h] [--outputdir OUTPUTDIR] [--timetolive TIMETOLIVE] --url URL
                  [--userdir USERDIR] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --outputdir OUTPUTDIR
                        path to output directory for logs and screenshots
  --timetolive TIMETOLIVE
                        time in milliseconds to wait before closing the browser
  --url URL             the URL to navigate to
  --userdir USERDIR     full path to a user browser data directory (temp or
                        persistent)
  --debug               turn on debugging messages
```
