# convert the same document to each of the supported versions; to allow comparing outputs
# results are placed in ./compare/; the original document is copied to ./compare/base.json
# each other output is named by the target version.

f_in=samples/20170213_297662.003.15.json
d_out=compare

mkdir -p $d_out
rm $d_out/*

cp "$f_in" "$d_out/base.json"

for version in $(python convert.py versions); do
  result="${d_out}/${version}.json"
  python convert.py convert "$f_in" "$result" -v? -t "$version" 2> /dev/null
done
