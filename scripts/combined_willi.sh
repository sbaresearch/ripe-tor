#! /bin/zsh
BASE_PATH=~/Documents/ripetor/run_willi/
IPV4_DE_INPUT=(${BASE_PATH}/combined-top-de/stat/combined*FROM-AS*.tex)
IPV4_US_INPUT=(${BASE_PATH}/combined-top-us/stat/combined*FROM-AS*.tex)

IPV4_OUTPUT=/home/havok/Documents/ripetor/run_gabriel/real_2022/combined-old

mkdir -p ${IPV4_OUTPUT}

# Remove all spaces and other funky characters from the latex tables
echo "Nospacing IPv4 DE input"
for i in ${IPV4_DE_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV4_OUTPUT}/DE_${filename}.nospace;
done

for i in ${IPV4_US_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV4_OUTPUT}/US_${filename}.nospace;
done

echo "IPv4: Extracting relevant values from all nospace files"
for i in ${IPV4_OUTPUT}/*nospace; do
  filename=$(basename $i)
  awk -F'&' '{if($3 >0 && $4 >0 && $5 >0){printf("%s %s %s \"%s\" \"%s\" \"%s\" \n",$3,$4,$5,$1,$2,FILENAME)}}' ${i} > ${IPV4_OUTPUT}/${filename}.values;
done

echo "IPv4: Combining all value files"
tail -qn +2 ${IPV4_OUTPUT}/*.values > ${IPV4_OUTPUT}/values.dat