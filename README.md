### python liftover utility

Converts point coordinates between genome assemblies.
Inspired by [pyliftover](https://github.com/konstantint/pyliftover), the primary
advantage this offers is dictionary style conversion, as in access converted
coordinates via `converter[chrom][pos]`.


### Installation
Install via pip: `pip install liftover`

### Usage

```python
from liftover import get_lifter

converter = get_lifter('hg19', 'hg38')
chrom = '1'
pos = 103786442
converter[chrom][pos]

converter.query(chrom, pos)
```
