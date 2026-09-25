#!/bin/sh
# Build the console as a program and lay the release bundle out:
#
#   console-<version>-x86_64-linux/
#     console        the launcher (bin/console)
#     console-bin    the program, built by `code build`
#     *.so           the organelles `euglena install` fetched, beside it
#     VERSION, README.md
#     app.info       what cdlvsm puts in the desktop's applications menu —
#                    and that it runs programs (`console -e program`), so
#                    cdlvsm opens terminal apps (the ide) in it
#
# The program is main.code without its organelle links: those would be
# built in as full paths on this machine, so the console links its organelles
# itself while it runs (see Organelles in src/app.gene.code).
#
#   tools/package.sh <version> <out-dir>        (after `euglena test`)
set -eu
version=$1
out=$2
root=$(cd "$(dirname "$0")/.." && pwd)
[ -f "$root/main.code" ] || { echo "no main.code — run euglena test first" >&2; exit 1; }
name="console-$version-x86_64-linux"
stage="$out/$name"
rm -rf "$stage"
mkdir -p "$stage"
grep -v '^link ".*\.so"' "$root/main.code" | grep -v '^| ' > "$root/standalone.code"
(cd "$root" && cdlvsm code build standalone.code -r -o "$stage/console-bin")
rm -f "$root/standalone.code"
cp "$root/bin/console" "$stage/console"
cp "$root/README.md" "$stage/"
"$root/tools/organelles.sh" "$stage"
echo "$version" > "$stage/VERSION"
cat > "$stage/app.info" <<'INFO'
name=codelovesme console
comment=A terminal in a window of its own
terminal=false
icon=utilities-terminal
categories=System;TerminalEmulator;
keywords=terminal;shell;command;codelovesme;
runs-programs=-e
INFO
tar -C "$out" -czf "$out/$name.tar.gz" "$name"
echo "$out/$name.tar.gz"
