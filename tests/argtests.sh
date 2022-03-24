#!/bin/bash
set -x
# Testing different variations of arguments to tomb raider

./tomb_raider.sh --dryrun --output-dir test --image dfrws-2006/dfrws-2006-challenge.raw
./tomb_raider.sh --dryrun --image dfrws-2006/dfrws-2006-challenge.raw
./tomb_raider.sh --dryrun --output-dir test /dev/null
./tomb_raider.sh --dryrun /dev/null
./tomb_raider.sh --dryrun --keep-image --output-dir test /dev/null
./tomb_raider.sh --dryrun --keep-image /dev/null
./tomb_raider.sh --dryrun --keep-image --output-dir test --image dfrws-2006/dfrws-2006-challenge.raw
./tomb_raider.sh --dryrun --keep-image --image dfrws-2006/dfrws-2006-challenge.raw

./tomb_raider.sh --dryrun /dev/null --keep-image --output-dir test /dev/null
./tomb_raider.sh --dryrun --not-an-argument --keep-image /dev/null


./tomb_raider.sh --dryrun 
./tomb_raider.sh --dryrun  --not-an-argument --keep-image
./tomb_raider.sh /dev/null --dryrun  --not-an-argument --keep-image
./tomb_raider.sh --dryrun  --not-an-argument --keep-image --image



./tomb_raider.sh --dryrun --image dfrws-2006/dfrws-2006-challenge.raw
./tomb_raider.sh --dryrun --output-dir test /dev/null
