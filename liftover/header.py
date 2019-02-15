
class ChainHeader(object):
    def __init__(self, line):
        fields = line.strip().split(' ')
        self.chain = fields[0]
        self.score = int(fields[1])
        self.target_id = fields[2]
        self.target_size = int(fields[3])
        self.target_strand = fields[4]
        self.target_start = int(fields[5])
        self.target_end = int(fields[6])
        self.query_id = fields[7]
        self.query_size = int(fields[8])
        self.query_strand = fields[9]
        self.query_start = int(fields[10])
        self.query_end = int(fields[11])
        self.id = fields[12]
        
        assert self.chain == 'chain', 'Invalid chain format. {}'.format(line)
        assert self.target_strand == '+', 'Target strand must be +. {}'.format(line)
        assert self.query_strand in ['+', '-'], 'Query strand must be - or +. {}'.format(line)
