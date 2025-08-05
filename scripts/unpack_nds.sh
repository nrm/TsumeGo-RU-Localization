mkdir data/full_extracted
docker run --rm -v $(pwd)/data:/work ndstool-builder ndstool -x /work/0558.nds -9 /work/full_extracted/arm9.bin -7 /work/full_extracted/arm7.bin -y9 /work/full_extracted/y9.bin -y7 /work/full_extracted/y7.bin -d /work/full_extracted/data -y /work/full_extracted/overlay -t /work/full_extracted/banner.bin -h /work/full_extracted/header.bin
