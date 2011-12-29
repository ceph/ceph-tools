"""
Bypass actual execution and produce an inventory of test cases,
with test-case descriptions based on defined annotation attributes.

This is a modified version of the standard collect.py plugin (for --collect-only)
"""
from nose.plugins.base import Plugin
from nose.case import Test
import logging
import unittest
import sys
import csv

log = logging.getLogger(__name__)

class TestInventory(Plugin):
    """
    Print an inventory of enabled tests,
    as annotated by specified properties.
    (probably best used with -q)
    """
    # default test description properties
    annoteProps = [ 'resource', 'method', 'operation', 'assertion' ]

    name = "test-inventory"
    enableOpt = 'inventory_only'
    outputFormat = 'json'
    numTests = 0

    def options(self, parser, env):
        """Register commandline options for this plugin.
        """
        parser.add_option('--test-inventory',
                          action='store_true',
                          dest=self.enableOpt,
                          help=self.help())

        parser.add_option('--test-inventory-properties',
                          action='store',
                          dest='propertyList',
                          default=env.get('NOSE_INVENTORY_PROPERTIES'),
                          help="%s\n[NOSE_INVENTORY_PROPERTIES]\n" %
                          "ordered list of comma-separated property names")

        parser.add_option('--test-inventory-format',
                          action='store',
                          dest='outputFormat',
                          default=env.get('NOSE_INVENTORY_FORMAT'),
                          help="supported formats are: col,csv,json\n[NOSE_INVENTORY_FORMAT]\n")


    def configure(self, options, config):
        """Figure out our annotation properties and output format
        """
        Plugin.configure(self, options, config)
        if options.propertyList != None:
            self.annoteProps = options.propertyList.split(',')
        log.debug("debug: Using annotation properties: %s" % self.annoteProps)

        if options.outputFormat == 'csv':
            self.outputFormat = 'csv'
            # CSV output should start with column headings
            sys.stderr.write('Test')
            for p in self.annoteProps:
                sys.stderr.write(',' + p)
            sys.stderr.write('\n')
        elif options.outputFormat == 'json':
            self.outputFormat = 'json'
        else:
            maxlen = 1
            for p in self.annoteProps:
                if p.__len__() > maxlen:
                    maxlen = p.__len__();
            self.outputFormat = '  %-' + '%d' % maxlen + 's %s\n'
        log.debug("debug: Using output format '%s'\n" % self.outputFormat);

    def prepareTestLoader(self, loader):
        """Install test-inventory suite class in TestLoader.
        """
        # Disable context awareness
        log.debug("Preparing test loader")
        loader.suiteClass = TestSuiteFactory(self.conf)

    def prepareTestCase(self, test):
        """Replace actual test with dummy that always passes.
        """
        # Return something that always passes
        log.debug("debug: Inventorying test case %s", test)
        if not isinstance(test, Test):
            return

        # print out the annotation properties
        self._describeTestCase(test)

        # pretend to run this test
        def run(result):
            # We need to make these plugin calls because there won't be
            # a result proxy, due to using a stripped-down test suite
            self.conf.plugins.startTest(test)
            result.startTest(test)
            self.conf.plugins.addSuccess(test)
            result.addSuccess(test)
            self.conf.plugins.stopTest(test)
            result.stopTest(test)
        return run

    def _describeTestCase(self, testcase):
        """Write out a description of the specified test-case
           (in terms of specified attributes, in configured format)
        """
        # the real testcase (with the annotation decorations) has
        # probably been wrapped by many plug-ins, so we have to
        # un-peel the onion to find the annotation attributes
        o = testcase
        while o != None:
            if hasattr(o, self.annoteProps[0]):
                break

            # stop when we run out of levels
            if hasattr(o, "test"):
                o = o.test
            else:
                o = None

        # we never found any annotation properties
        if o == None:
            # in collumn format, we list all test cases
            if self.outputFormat != 'json' and self.outputFormat != 'csv':
                sys.stderr.write("Test Case: %s\n" % testcase);
            return

        # write out the properties as quoted comman separated values
        if self.outputFormat == 'csv':
            # write out the properties as quoted comma separated values
            sys.stderr.write("'%s'" % testcase)
            for p in self.annoteProps:
                sys.stderr.write(",")
                value = getattr(o, p, None)
                if value != None:
                    sys.stderr.write("'" + value + "'")
            sys.stderr.write("\n");

        # write out the properties in json
        elif self.outputFormat == 'json':
            if self.numTests > 0:
                sys.stderr.write(",")
            else:
                sys.stderr.write("[")
            sys.stderr.write("\n\t{\n")
            sys.stderr.write("\t\ttestcase: \"%s\"" % testcase)
            for p in self.annoteProps:
                value = getattr(o, p, None)
                if value == None:
                    continue
                sys.stderr.write(",")
                sys.stderr.write("\n\t\t%s: \"%s\"" % (p, value))
            sys.stderr.write("\n\t}");
            self.numTests += 1

        # write out the properties in neat cols under the test name
        else:
            sys.stderr.write("Test Case: %s\n" % testcase);
            for p in self.annoteProps:
                if hasattr(o, p):
                    value = getattr(o, p, "True")
                    sys.stderr.write(self.outputFormat % (p, value))

    def report(self,  stream):
        """ Called after all tests have run to produce final output
        """
        if self.outputFormat == 'json':
            sys.stderr.write("\n]\n")

class TestSuiteFactory:
    """
    Factory for producing configured test suites.
    """
    def __init__(self, conf):
        self.conf = conf

    def __call__(self, tests=(), **kw):
        return TestSuite(tests, conf=self.conf)


class TestSuite(unittest.TestSuite):
    """
    Basic test suite that bypasses most proxy and plugin calls, but does
    wrap tests in a nose.case.Test so prepareTestCase will be called.
    """
    def __init__(self, tests=(), conf=None):
        self.conf = conf
        # Exec lazy suites: makes discovery depth-first
        if callable(tests):
            tests = tests()
        log.debug("TestSuite(%r)", tests)
        unittest.TestSuite.__init__(self, tests)

    def addTest(self, test):
        if isinstance(test, unittest.TestSuite):
            self._tests.append(test)
        else:
            self._tests.append(Test(test, config=self.conf))
