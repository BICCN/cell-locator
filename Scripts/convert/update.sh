# update all files in ./samples/ to the latest supported version.
# results are placed in ./update/ with the same filenames

d_in=samples
d_out=update

mkdir -p $d_out

for sample in $d_in/*.json; do
  result="${d_out}/${sample##*/}"
  python convert.py convert "$sample" "$result" -v? -i 2> /dev/null
done
