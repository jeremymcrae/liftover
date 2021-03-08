![liftover](https://github.com/jeremymcrae/liftover/workflows/liftover/badge.svg)

### python liftover utility

Converts point coordinates between genome assemblies.
Inspired by [pyliftover](https://github.com/konstantint/pyliftover), this
offers a few advantages:
 - ~5X faster, and lower memory requirements, as loading the chain file and
   converting coordinates is implemented in c++.
 - dictionary style conversion, as in access converted coordinates via
   `converter[chrom][pos]`

### Installation
Install via pip: `pip install liftover`

### Usage

```python
from liftover import get_lifter

converter = get_lifter('hg19', 'hg38')
chrom = '1'
pos = 103786442
converter[chrom][pos]

# other synonyms for the lift call
converter.convert_coordinate(chrom, pos)
converter.query(chrom, pos)

# alternatively create a converter directly from a chainfile
from liftover import ChainFile
converter = ChainFile('/home/user/hg18ToHg38.over.chain.gz', 'hg18', 'hg38')
converter[chrom][pos]
```

