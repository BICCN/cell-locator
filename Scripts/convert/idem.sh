# idempotency test. convert each file in ./samples/ to its own version
# ideally this would leave each file unchanged, however some changes will occur
# results are placed in ./idem/; then meld https://meldmerge.org/ is invoked to show
# a diff of all the changes

d_in=samples
d_out=idem

mkdir -p $d_out
rm $d_out/*

for sample in $d_in/*.json; do
  result="${d_out}/${sample##*/}"
  version=$(python convert.py infer "$sample")
  python convert.py convert "$sample" "$result" -v "$version" -t "$version" -i
done

meld "$d_in" "$d_out" 2> /dev/null
