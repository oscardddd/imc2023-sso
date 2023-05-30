#!/usr/bin/env python3
import unittest
import os
import glob
from templatematch import TemplateMatcher

class TemplateMatchTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TemplateMatchTest, self).__init__(*args, **kwargs)
        self.matcher = TemplateMatcher("templates/")

    def test_nomatch_expected(self):
        print("")

        image_count = 18

        images = os.path.join("test-data/no_sso/", '*.png')
        image_files = glob.glob(images)

        self.assertEqual(image_count, len(image_files), f"Expect {image_count} test images")

        for test_image in image_files:
            print("\ttesting %s" % test_image)
            results = self.matcher.matchfile(test_image)
            self.assertEqual(0, len(results), "Expected no matching results in %s but got %s" % (test_image, ', '.join([x.oauth_provider for x in results])))

    def test_spotify(self):
         self.assert_expected("spotify.png", ["facebook", "apple", "google"])

    def test_onlyfans(self):
        self.assert_expected("onlyfans.png", ["twitter", "google", "microsoft"])

    def test_twitter(self):
        self.assert_expected("twitter.png", ["twitter", "google", "apple"])

    def test_carfax(self):
        self.assert_expected("carfax.png", ["google", "facebook", "apple"])

    def test_delish(self):
        self.assert_expected("delish.png", ["facebook", "google", "apple"])

    def test_ultimateguitar(self):
        self.assert_expected("ultimate-guitar.png", ["facebook", "google", "apple"])

    def test_stackoverflow(self):
        self.assert_expected("stackoverflow.png", ["google", "github", "facebook"])

    def test_vimeo(self):
        self.assert_expected("vimeo.png", ["facebook", "google", "apple"])

    def test_yelp(self):
        self.assert_expected("yelp.png", ["facebook", "google", "apple"])

    def test_adam4adam(self):
        self.assert_expected("adam4adam.png", ["facebook", "google", "apple"])

    def test_bedbathandbeyond(self):
        self.assert_expected("bedbathandbeyond.png", ["facebook", "google", "apple"])

    def test_baseball_reference(self):
        self.assert_expected("baseball-reference.png", ["facebook", "google"])

    def test_nintendo(self):
        self.assert_expected("nintendo.png", ["google", "apple"])

    def test_medium(self):
        self.assert_expected("medium.png", ["google", "apple", "facebook", "twitter"])

    def test_fantasypros(self):
        self.assert_expected("fantasypros.png", ["facebook", "apple"])

    def test_washingtonpost(self):
        self.assert_expected("washingtonpost.png", ["amazon", "google", "facebook", "apple"])
    
    def test_latimes(self):
        self.assert_expected("latimes.png", ["microsoft", "google", "facebook", "apple", "twitter", "yahoo"])
    
    def test_grubhub(self):
        self.assert_expected("grubhub.png", ["facebook", "google", "amazon"])

    def test_glassdoor(self):
        self.assert_expected("glassdoor.png", ["facebook", "google"])

    def test_khanacademy(self):
        self.assert_expected("khanacademy.png", ["facebook", "google", "apple"])

    def test_newsweek(self):
        self.assert_expected("newsweek.png", ["facebook", "google", "apple", "amazon"])
    
    def test_webtoons(self):
        self.assert_expected("webtoons.png", ["facebook", "google", "apple", "twitter"])

    def assert_expected(self, test_image_name: str, expected_oauth_list: list[str]):
        print("")
        print("\ttesting %s contains %s" % (test_image_name, ', '.join(expected_oauth_list)))

        results = self.matcher.matchfile("test-data/sso/" + test_image_name)

        oauth_results = set([x.oauth_provider for x in results])
        expeected_results = set(expected_oauth_list)

        self.assertSetEqual(oauth_results, expeected_results, "Expected '%s' providers but got '%s'" % (', '.join(expeected_results), ', '.join(oauth_results)))

if __name__ == '__main__':
    unittest.main(verbosity=2)