filepath="config/chains"
searchstring="eth_balance_amount"
replacestring="balance_amount"

for file in $(grep -l -R $searchstring $filepath)
do
  sed -e "s/$searchstring/$replacestring/ig" $file > tempfile.tmp
  mv tempfile.tmp $file
  chmod 755 $file

  echo "Modified: " $file
done

source scripts/reset_redis.sh