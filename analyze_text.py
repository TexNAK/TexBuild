#!/usr/bin/env python3
import re
import os
import sys
import subprocess
import spellchecker

from github import Github


class REMatcher(object):
    def __init__(self, matchstring):
        self.matchstring = matchstring
        self.rematch = None

    def match(self, regexp):
        self.rematch = re.match(regexp, self.matchstring)
        return bool(self.rematch)

    def group(self, i):
        return self.rematch.group(i)


def get_texcount_output(dockercmd, directory, file):
    res = subprocess.run([dockercmd, 'texcount -freq -merge -stat -dir=/data /data/' + file], stdout=subprocess.PIPE, cwd=directory)
    return res.stdout.decode('utf-8')


def parse_preamble(preamble):
    res = ""

    res += '### Overall statistics\n'
    res += '|   | Count |\n'
    res += '| - | ----- |\n'

    for line in preamble.splitlines()[2:]:
        parts = line.split(": ")
        res += '| ' + parts[0] + ' | ' + parts[1] + ' |\n'

    res += '\n\n'

    return res


def parse_headers(headers):
    res = ""
    indent_unit = "&nbsp;&nbsp;&nbsp;&nbsp;"
    r = re.compile('  (\\d+)\\+\\d+\\+\\d+ \\(\\d+/(\\d+)/(\\d+)/(\\d+)\\) (\\w+): (.*)', re.DOTALL)

    res += '### Statistics grouped by header\n'
    res += "| Header | Word count | Floats | Math (inline) | Math (displayed) |\n"
    res += "| - | - | - | - | - |\n"
    for line in headers.splitlines():
        header_indent = ""
        m = REMatcher(line)
        if m.match(r):
            word_count = m.group(1)
            float_count = m.group(2)
            inline_math = m.group(3)
            displayed_math = m.group(4)
            header_type = m.group(5)
            header_title = m.group(6)

            if header_type == "Chapter":
                header_indent = indent_unit
            elif header_type == "Section":
                header_indent = indent_unit * 2
            elif header_type == "Subsection":
                header_indent = indent_unit * 3

            res += '| ' + header_indent + header_title + ' | ' + word_count + ' | ' + float_count + ' | ' + inline_math + ' | ' + displayed_math + ' |\n'
    res += '\n\n'

    return res


def parse_word_frequency(word_frequency):
    res = ""

    res += '### Top 10 words\n'
    res += '|   | Count |\n'
    res += '| - | ----- |\n'
    for word in word_frequency.splitlines()[:10]:
        parts = word.split(": ")
        res += '| ' + parts[0] + ' | ' + parts[1] + '|\n'

    res += '\n\n'

    return res


def process_texcount_output(output):
    m = REMatcher(output)
    r = re.compile('(.*)Subcounts:\\n  text\\+headers\\+captions \\(#headers\\/#floats\\/#inlines\\/#displayed\\)\\n(.*)\\nWord: Freq\\n---\\n(.*)\\n---\\n(.*)\\nSum of subset:', re.DOTALL)

    res = ""

    if m.match(r):
        # Group 1: Preamble (Overall stats, Encoding)
        # Group 2: Headers and their individual stats
        # Group 3: Word statistics
        # Group 4: Word frequency table
        res += parse_preamble(m.group(1))
        res += parse_headers(m.group(2))
        # res += parse_word_stats(m.group(3))
        # res += parse_word_frequency(m.group(4))

    return res


# Arguments:
# 1. GitHub Access Token
# 2. Repository slug (org/repo)
# 3. Pull request ID
# 4. Main .tex file
githubToken = sys.argv[1]
organization = sys.argv[2].split('/')[0]
repository = sys.argv[2].split('/')[1]
pullReqID = sys.argv[3]
files = sys.argv[4:]

scriptPath = os.path.dirname(os.path.realpath(__file__))

if "false" == pullReqID:
    print("This is not a Pull Request build. Skipping document analysis!")
    exit(1)
else:
    pullReqID = int(pullReqID)

print("Organization:\t" + organization)
print("Repository:\t" + repository)
print("Pull request:\t" + str(pullReqID))
print("Files:\t\t" + str(files))

g = Github(githubToken)

pullReq = g.get_organization(organization).get_repo(repository).get_pull(pullReqID)

if not pullReq:
    print("Pull request not found!")
    exit(1)

for file in files:
    folder = os.path.dirname(os.path.abspath(file))
    filename = os.path.basename(file)

    markdownCode = "# Document analysis (" + filename + ")\n\n"
    markdownCode += "## Grammar check\n\n"
    markdownCode += spellchecker.spellcheck_pdfs(folder)

    markdownCode += "\n\n___\n\n"

    markdownCode += "## Statistics\n\n"
    texcount_output = get_texcount_output(scriptPath + "/dockercmd.sh", folder, filename)
    markdownCode += process_texcount_output(texcount_output)

    print("\nCommenting on GitHub ...")
    pullReq.create_issue_comment(markdownCode)
