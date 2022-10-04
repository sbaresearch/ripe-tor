#! /bin/zsh
BASE_PATH=~/Documents/ripetor/run_gabriel

IPV4_DE_INPUT=(${BASE_PATH}/*multi_germany_ipv4/stat/combined*FROM-AS*.tex)
IPV4_US_INPUT=(${BASE_PATH}/*multi_usa_ipv4/stat/combined*FROM-AS*.tex)
IPV6_DE_INPUT=(${BASE_PATH}/*multi_germany_ipv6/stat/combined*FROM-AS*.tex)
IPV6_US_INPUT=(${BASE_PATH}/*multi_usa_ipv6/stat/combined*FROM-AS*.tex)
IPV4_RU_INPUT=(${BASE_PATH}/20220919-143112_multi_russia_ipv4/stat/combined*FROM-AS*.tex)
IPV6_RU_INPUT=(${BASE_PATH}/20220919-205747_multi_russia_ipv6/stat/combined*FROM-AS*.tex)

IPV4_OUTPUT=/home/havok/Documents/ripetor/run_gabriel/real_2022/combined-us-v4
IPV6_OUTPUT=/home/havok/Documents/ripetor/run_gabriel/real_2022/combined-us-v6
mkdir -p ${IPV4_OUTPUT} ${IPV6_OUTPUT}

# Remove all spaces and other funky characters from the latex tables
echo "Nospacing IPv4 DE input"
for i in ${IPV4_DE_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV4_OUTPUT}/DE_${filename}.nospace;
done

echo "Nospacing IPv4 US input"
for i in ${IPV4_US_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV4_OUTPUT}/US_${filename}.nospace;
done

echo "Nospacing IPv6 DE input"
for i in ${IPV6_DE_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV6_OUTPUT}/DE_${filename}.nospace;
done

echo "Nospacing IPv6 US input"
for i in ${IPV6_US_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV6_OUTPUT}/US_${filename}.nospace;
done

echo "Nospacing IPv4 RU input"
for i in ${IPV4_RU_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV4_OUTPUT}/RU_${filename}.nospace;
done

echo "Nospacing IPv6 RU input"
for i in ${IPV6_RU_INPUT}; do
  filename=$(basename $i)
  sed -e 's/[[:space:]]//g' -e 's/\\//g' ${i} > ${IPV6_OUTPUT}/RU_${filename}.nospace;
done

echo "IPv4: Extracting relevant values from all nospace files"
for i in ${IPV4_OUTPUT}/*nospace; do
  filename=$(basename $i)
  awk -F'&' '{if($3 >0 && $4 >0 && $5 >0){printf("%s %s %s \"%s\" \"%s\" \"%s\" \n",$3,$4,$5,$1,$2,FILENAME)}}' ${i} > ${IPV4_OUTPUT}/${filename}.values;
done

echo "IPv6: Extracting relevant values from all nospace files"
for i in ${IPV6_OUTPUT}/*nospace; do
  filename=$(basename $i)
  awk -F'&' '{if($3 >0 && $4 >0 && $5 >0){printf("%s %s %s \"%s\" \"%s\" \"%s\" \n",$3,$4,$5,$1,$2,FILENAME)}}' ${i}> ${IPV6_OUTPUT}/${filename}.values;
done

echo "IPv4: Combining all value files"
tail -qn +2 ${IPV4_OUTPUT}/*.values > ${IPV4_OUTPUT}/values.dat

echo "IPv6: Combining all value files"
tail -qn +2 ${IPV6_OUTPUT}/*.values > ${IPV6_OUTPUT}/values.dat