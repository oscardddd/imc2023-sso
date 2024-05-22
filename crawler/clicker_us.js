#!/usr/bin/env node

"require strict";

import normalizeUrl from "normalize-url";
import filenamify from "filenamify";
import log from "loglevel";

// we need both `import` (ES6) and `require` (CommonJS)
// <https://stackoverflow.com/a/61947868>
import { createRequire } from "module";
import { Console } from "console";
const require = createRequire(import.meta.url);

const { ArgumentParser } = require("argparse");
const path = require("path");
const fs = require("fs");
const zlib = require("zlib");

const { chromium } = require("playwright-extra");
const stealth = require("puppeteer-extra-plugin-stealth")();
chromium.use(stealth);

(async () => {
  function toSortableDateTime(datetime) {
    let iso8601 = datetime.toISOString();
    return iso8601.replace(/T|Z|-|:|\./g, ""); // 2021-09-28T07:43:03.645Z => 20210928074303645
  }

  function generateFilename(url, expnote = "") {
    let normedUrl = normalizeUrl(url, { stripWWW: false }); // www and protocol makes a difference
    let convertedUrl = filenamify(decodeURIComponent(normedUrl));
    let formattedDateTime = toSortableDateTime(new Date());
    if (expnote) {
      return expnote + "-" + convertedUrl + "-" + formattedDateTime;
    }
    return convertedUrl + "-" + formattedDateTime;
  }

  function saveCompressedString(filename, str) {
    const gzip = zlib.createGzip();
    const out = fs.createWriteStream(filename);
    gzip.pipe(out);
    gzip.write(str);
    gzip.end();
  }

  async function closeAndExit(browser) {
    console.error("[.] closeAndExit called");
    await browser.close();
    process.exit(0);
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function clickButton(page, buttonLabel) {
    let frames = page.frames(); // button can be in an iframe so search all
    let found = false;

    for (let i = 0; i < frames.length; i++) {
      let frame = frames[i];
      let searchSelector = "text=" + buttonLabel;

      let button = frame.locator(searchSelector);

      try {
        await button.click({ timeout: 5000, strict: false });
        found = true;
        break;
      } catch (error) {
        if (error.name === "TimeoutError") {
          continue; // Button not found on this frame
        } else {
          throw error; // Unexpected error
        }
      }
    }

    if (!found) {
      throw new Error("Button not found: " + buttonLabel);
    }
  }

  async function findButton(page, buttonLabel) {
    let frames = page.frames(); // button can be in an iframe so search all

    console.debug(
      '[.] Searching for "' + buttonLabel + '" in ' + frames.length + " frames."
    );
    let searchSelector = "text=" + buttonLabel;

    for (let i = 0; i < frames.length; i++) {
      let frame = frames[i];

      try {
        const element = await frame.waitForSelector(searchSelector, {
          strict: false,
          state: "attached",
          timeout: 1000,
        });

        //console.log(element);
        //if((element.getAttribute('onclick')===null)&&(element.getAttribute('href')===null)){
        //    // not clickable
        //   console.error("[.] Found non-clickable match so skipping.");
        //   continue;
        //}

        return true;
      } catch (error) {
        if (error.name === "TimeoutError") {
          continue; // Button not found on this frame
        } else if (error.message.includes("frame got detached")) {
          console.error(error);
          continue; // frames related to ads seem to come and go so just continue
        } else {
          throw error; // Unexpected error
        }
      }
    }

    return false;
  }

  async function findInputUsername(page) {
    let frames = page.frames(); // button can be in an iframe so search all

    for (let i = 0; i < frames.length; i++) {
      log.error(`[..] current frame: ${i} (total: ${frames.length})`);
      let frame = frames[i];

      // TODO() most username fields are named "username",
      // but that might not always be the case.

      try {
        let inputs = await frame.locator(
          'input[name="username"] >> visible=true'
        );
        await inputs.waitFor({ timeout: 800 }); // XXX
        let count = await inputs.count();
        log.debug(`[..] ${count} username fields = ${inputs}`);

        if (count > 0) {
          return true;
        }
      } catch {} // timeout reached, go to next frame
    }

    return false;
  }

  async function findInputPassword(page) {
    let frames = page.frames(); // button can be in an iframe so search all

    for (let i = 0; i < frames.length; i++) {
      log.error(`[..] current frame: ${i} (total: ${frames.length})`);
      let frame = frames[i];

      try {
        let inputs = await frame.locator('input[type="password"]');
        await inputs.waitFor({ timeout: 800 }); // XXX
        let count = await inputs.count();
        log.debug(`[..] ${count} password fields = ${inputs}`);

        // TODO() are any input[type=password] fields invisible?
        if (count > 0) {
          return true;
        }
      } catch {} // timeout reached, go to next frame
    }

    return false;
  }

  async function findButtons(page, buttonLabels) {
    // <https://playwright.dev/docs/api/class-page#page-frames>
    //
    // XXX() this should work when we have "simple" pages, but
    // will take more thought on dynamically changing websites (do
    // we have an example?)
    //
    // each `frame` in page.frames() might not have a unique name or
    // ID, and it's possible that each call to `page.frames()`
    // returns a different set.
    //
    let frames = page.frames(); // button can be in an iframe so search all
    let results = [];

    // build our search selector
    var searchSelector = "";
    var searchSelector2 = "";
    var searchSelector3 = "";
    for (let i = 0; i < buttonLabels.length; i++) {
      searchSelector += "text=" + buttonLabels[i];
      searchSelector2 += "@aria-label=" + buttonLabels[i];
      if (i != buttonLabels.length - 1) {
        searchSelector += ", ";
        searchSelector2 += ", ";
      }
    }

    // no xpath or css
    searchSelector3 = buttonLabels[0];

    searchSelector += " >> visible=true";
    searchSelector2 += " >> visible=true";

    // TODO() it's possible that we have frames inside frames,
    // so we'd need to recursively search (and bounce after 2 or 3
    // levels to avoid infinite recursion)
    for (let i = 0; i < frames.length; i++) {
      log.error(`[..] current frame: ${i} (total: ${frames.length})`);
      let frame = frames[i];

      log.debug(`[..] looking for "${searchSelector}"`);

      var buttons;
      var count;

      try {
        // aria-label a work in progress 2023-05-24
        //buttons = await (frame.locator(searchSelector)).or(frame.getByText(searchSelector3)).or(frame.getByLabel(searchSelector3));
        buttons = await frame.locator(searchSelector);

        // count does not have a timeout, and some pages hang on
        // searching. so we'll try to resolve the locator with a low
        // timeout. if it times out, then we can assume that the count
        // is 0.
        //
        // See <https://github.com/microsoft/playwright/issues/9224>
        try {
          await buttons.first().waitFor({ timeout: 500 });
          count = await buttons.count();
        } catch (e) {
          log.error(`[..] ${e}`);
          count = 0;
        }
      } catch (error) {
        if (error.name === "TimeoutError") {
          continue; // Button not found on this frame
        } else if (error.message.includes("frame got detached")) {
          log.error(error);
          continue; // frames related to ads seem to come and go so just continue
        } else {
          throw error; // Unexpected error
        }
      }

      log.debug(`[..] count = ${count}`);

      // start clicking
      for (let j = 0; j < count; j++) {
        log.debug(`[..] processing button ${j}`);

        // TODO() it would be great for debugging to try
        // and highlight the button in red.
        //
        //let eh = await buttons.nth(j).elementHandle();
        //await eh.evaluate(node => node.setAttribute('style', 'border:1px;border-style:solid;border-color:#FF0000;padding:10px'));
        //log.debug(`${await eh.evaluate(node => node.getAttribute("href"))}`);
        //log.debug(`${await frame.evaluate(node => node.getAttribute("href"), eh)}`);

        let button = buttons.nth(j);
        let buttonVisible = await button.isVisible();
        log.debug(`[...] visible? ${buttonVisible}`);

        try {
          if (buttonVisible === true) {
            log.debug(`[...] found button ${j}, adding it to array`);
            results.push(button);
          } else {
            log.debug(`[...] element is hidden, skipping`);
          }
        } catch (error) {
          log.debug(`[...] error occured, contuing to next button`);
          log.debug(`${error}`);
          continue;
        }
      }
    }

    // if we have no matching elements, return false
    return results;
  }

  // argparse: parse arguments
  const parser = new ArgumentParser({});

  parser.add_argument("--headless", {
    action: "store_true",
    required: false,
    help: "don't show GUI",
  });

  parser.add_argument("--outputdir", {
    type: "str",
    required: false,
    help: "path to output directory for logs and screenshots",
    default: "output",
  });

  parser.add_argument("--outputprefix", {
    type: "str",
    required: false,
    help: "prefix for files and logs (e.g., exp notes, etc)",
    default: "default",
  });

  parser.add_argument("--timetolive", {
    type: "int",
    required: false,
    help: "time in milliseconds to wait before closing the browser",
    default: 5 * 1000,
  });

  parser.add_argument("--url", {
    type: "str",
    required: true,
    help: "the URL to navigate to",
  });

  parser.add_argument("--userdir", {
    type: "str",
    required: false,
    help: "full path to a user browser data directory (temp or persistent)",
    default: "/tmp",
  });

  parser.add_argument("--debug", {
    action: "store_true",
    required: false,
    help: "turn on debugging messages",
  });

  const args = parser.parse_args();

  const outputDir = args.outputdir;
  const outputPrefix = args.outputprefix;
  const timeToLive = args.timetolive;
  var url = args.url;
  const userDataDir = args.userdir;

  const debug = args.debug;
  const headless = args.headless;

  const expStartDt = new Date();

  const outputFilenameBase = generateFilename(url, outputPrefix);

  if (debug) {
    log.setLevel(log.levels.DEBUG);
    log.debug("[.] debugging turned on");
  } else {
    log.setLevel(log.levels.ERROR);
  }

  let browserArgs = [];
  if (headless) {
    // <https://playwright.dev/docs/chrome-extensions>
    // need to use new parameter to load extensions in headless mode
    browserArgs.push(`--headless=chrome`);
  }

  browserArgs.push(`--disable-infobars`);
  browserArgs.push(`--disable-notifications`);

  // anti-anti-bot detection
  browserArgs.push(`--disable-blink-features`);
  browserArgs.push(`--disable-blink-features=AutomationControlled`);

  // XXX() by default (as of 2023-01-31) we'll use the I still
  // don't care about cookies extension to block cookie banners
  //
  // it also looks like you need both "disable-extensions..." and
  // "load-extension"?
  let pathToISDCAC = require("path").join(path.resolve(), "isdcac-v1.10");
  browserArgs.push(`--disable-extensions-except=${pathToISDCAC}`);
  browserArgs.push(`--load-extension=${pathToISDCAC}`);

  log.debug(`[.] path to extension: ${browserArgs}`);

  let ignoreBrowserArgs = [];

  // anti-anti-bot detection
  //
  // to stop the info banner + other switches that could be used to
  // detect as a bot?
  //
  // this also sets navigator.webdriver to false
  ignoreBrowserArgs.push(`--enable-automation`);

  // XXX() some websites (like github.com) hide elements
  // that we care about (like the sign in button) if the resolution
  // is too small.
  /*const browser = await chromium.launchPersistentContext(
        userDataDir,
        {
            args: browserArgs,
            headless: headless,
            viewport: {'width': 1920, 'height': 1080},
            userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
            recordHar: { path: outputDir + '/' + outputFilenameBase + '.har'},
        });//*/

  // switch to using the default incognito window instead of a
  // persistent context as somehow cloudflare breaks on the latter
  const browser = await chromium.launch({
    args: browserArgs,
    channel: "chrome",
    headless: false,
    ignoreDefaultArgs: ignoreBrowserArgs,
    viewport: null,
  });

  // only for persistent contexts
  /*
    // Chromium opens with a tab already so get the existing page instead of creating a new one
    var [page] = await browser.pages();  // the alternative that opens a new tab: const page = await browser.newPage();
    // resize viewport
    await page.setViewportSize({ width: 1920, height: 1080 });/*/

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
  });

  // catch ^C to cleanly exit
  process.on("SIGINT", async function () {
    console.log("[.] caught Ctrl-C, exiting");
    await page.close();
    await browser.close();
    process.exit(0);
  });

  await sleep(2000); // give browser a chance to finish loading

  // page.goto expects a scheme in the URL, so ensure that we have one
  //
  // TODO() force http:// or https://?
  //
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }

  console.error(`[.] opening ${url}`);
  await page.goto(url, { waitUntil: "load", timeout: 60 * 1000 }); // nytimes doesn't load in 30 seconds right now

  console.error(
    `[.] waiting for timeout ${timeToLive} ms before trying to search`
  );
  await page.waitForTimeout(timeToLive);

  log.info(`[.] take a screenshot`);
  await page.screenshot({
    path: outputDir + "/" + outputFilenameBase + "-0.png",
  });

  log.info(`[.] saving html`);
  const html0 = await page.content();
  saveCompressedString(
    outputDir + "/" + outputFilenameBase + "-0.html.gz",
    html0
  );

  // detect login page or login buttons //////////////////////////////////////
  //
  // the landing page can have:
  // 1. username field only + login button
  // 2. username and password fields + login button
  // 3. a link or button to log in
  //
  // we attempt to handle each of those cases below, in order.

  log.error(`[.] detect login page or buttons`);

  // landing page case (1) and (2)
  log.error(`[..] is the landing page a login page?`);
  let inputUsernameFound = await findInputUsername(page);
  log.info(`[..] found input[name="username"] = ${inputUsernameFound}`);

  if (inputUsernameFound == false) {
    log.error(
      `[..] could not find input[name="username"], trying login buttons next`
    );
  } else {
    log.error(
      `[..] found input[name="username"], looking for oAuth providers next`
    );
  }

  // landing page case (3)
  if (inputUsernameFound == false) {
    // TODO() break next section into its own function
    log.error(`[.] Searching for Log In buttons`);

    // matches {"Login","Log in"}, "Sign in", "Account", or "My XXXX" (e.g, "my account" or "my hulu")
    //
    // "My\\s*[a-zA-Z]" doesn't quite work because "My Appraisal"
    // (edmunds[.]com) would satisfy this
    let loginButtonLabels = ["/(Log\\s*in|Sign in|Account|My\\s*Account+)/i"];

    let loginButtonsFound = await findButtons(page, loginButtonLabels);
    log.debug(`[.] found buttons = ${loginButtonsFound}`);

    if (loginButtonsFound.length == 0) {
      // TODO() we should also output a log entry
      log.error(`[.] could not find any login or sign in buttons on ${url}.`);
      // await closeAndExit(browser);
    } else {
      log.info(
        `[.] found ${loginButtonsFound.length} buttons, clicking on all until the page changes`
      );

      // TODO() often a login button leads to a new page, but sometimes
      // it opens up a "dialog box" on the same page. this could lead to
      // odd behavior if we are clicking on multiple buttons.
      for (let i = 0; i < loginButtonsFound.length; i++) {
        try {
          log.error(`[..] trying to click on button ${i}`);
          await loginButtonsFound[i].click({ timeout: 2 * 1000 });
        } catch (error) {
          if (error.name === "TimeoutError") {
            continue; // Button not found on this frame
          } else if (error.message.includes("frame got detached")) {
            log.error(`[..] could not click as frame got detached, continuing`);
            continue; // frames related to ads seem to come and go so just continue
          } else {
            throw error; // Unexpected error
          }
        }

        // pause a bit to let things load and change
        await sleep(3 * 1000);

        // assume we are successful, so stop clicking buttons
        break;
      }
    }
  }

  // DETECT PAGE CHANGE //////////////////////////////////////////////
  //
  // three (?) possible things can happen here:
  // 1. URL changes (example.com -> example.com/login)
  // 2. "dialog box" appears with username/password + oauth fields
  // 3. nothing
  //
  // TODO() we should figure out what happens and output it in a log
  // entry
  let loginUrl = await page.url();

  log.info(`[.] take another screenshot`);
  await page.screenshot({
    path: outputDir + "/" + outputFilenameBase + "-1.png",
  });

  log.info(`[.] saving another html`);
  const html1 = await page.content();
  saveCompressedString(
    outputDir + "/" + outputFilenameBase + "-1.html.gz",
    html1
  );

  // OAUTH SEARCH ////////////////////////////////////////////////////

  // XXX() new oauth providers need to go at the end!
  let oauthProviders = [
    "Amazon",
    "Apple",
    "GitHub",
    "Google",
    "Facebook",
    "LinkedIn",
    "Microsoft",
    "Twitter",
    "Yahoo",
  ];
  let oauthButtonLabelTemplates = [
    "Sign up with",
    "Sign in with",
    "Continue with",
    "Log in with",
    "Login with",
    "Register with",
  ];

  let oauthProvidersRegex = "(" + oauthProviders.join("|") + ")";
  let oauthButtonLabelRegex = "(" + oauthButtonLabelTemplates.join("|") + ")";

  let oauthRegex =
    "/(" + oauthButtonLabelRegex + "\\s+" + oauthProvidersRegex + ")/i";
  log.debug(`[.] regex used = ${oauthRegex}`);

  let oauthButtonsFound = await findButtons(page, [oauthRegex]);
  log.info(`[.] found ${oauthButtonsFound.length} oauth buttons`);
  log.debug(`[.] oauth buttons = ${oauthButtonsFound}`);

  // iterate through the buttons and print matches
  let oauthProvidersRe = new RegExp(oauthProvidersRegex, "gi");

  var resultsOauth = [];
  for (let i = 0; i < oauthButtonsFound.length; i++) {
    // get all innerTexts in case there's some crazy nested div/span thing
    // going on
    let buttonTexts = await oauthButtonsFound[i].allInnerTexts(); // array
    log.debug(`[..] button ${i}: allInnerTexts() = ${buttonTexts}`);

    for (let j = 0; j < buttonTexts.length; j++) {
      let oauthProvidersFound = buttonTexts[j].match(oauthProvidersRe);
      log.debug(`[..] button ${i}: oauth providers = ${oauthProvidersFound}`);
      resultsOauth.push(oauthProvidersFound);
    }
  }

  // FIRST PARTY AUTH SEARCH /////////////////////////////////////////
  let firstPartyAuth = await findInputPassword(page);
  if (firstPartyAuth === true) {
    resultsOauth.push("FirstPartyAuth");
  }

  log.debug(`[.] oauth providers = ${resultsOauth}`);

  // OUTPUT //////////////////////////////////////////////////////////

  // convert list of oauth providers to 0s and 1s
  //
  // XXX() addng "support" for new oauth providers gets a bit dicey.
  // for now, it'd be appended to the end and strict ordering matters!
  //
  // format:
  //   "1st"|"Amazon"|"Apple"|"GitHub"|"Google"|"Facebook"|"LinkedIn"|"Microsoft"|"Twitter"|"Yahoo"
  // example:
  //   1|0|0|0|0|1|0|1|0|1
  //
  // XXX() this code is probably inefficient :-)
  //
  var tempOauthProviders = ["FirstPartyAuth"].concat(oauthProviders);
  var oauthProvidersBinary = [];
  for (let i = 0; i < tempOauthProviders.length; i++) {
    let found = resultsOauth.find((element) => {
      return (
        element.toString().toLowerCase() === tempOauthProviders[i].toLowerCase()
      );
    });

    if (found) {
      oauthProvidersBinary.push(1);
    } else {
      oauthProvidersBinary.push(0);
    }
  }

  // CSV header:
  //
  // outputPrefix,timestamp,url,login_url,screenshot_url,screenshot_login_url,1st,amazon,apple,github,google,facebook,linkedin,microsoft,twitter,yahoo
  //
  console.log(
    `${outputPrefix},${expStartDt.toISOString()},${url},${loginUrl},${outputFilenameBase}-0.png,${outputFilenameBase}-1.png,${outputFilenameBase}-0.html.gz,${outputFilenameBase}-1.html.gz,${oauthProvidersBinary.join(
      ","
    )}`
  );

  // CLEANUP AND EXIT ////////////////////////////////////////////////
  if (debug === true) {
    log.info(`[.] sleeping for 30s for debugging`);
    await sleep(30 * 1000);
  }
  await closeAndExit(browser);
})();
