# Moved from Paulihedral
class pNode:
    def __init__(self, idx):
        # self.child = []
        self.idx = idx
        self.adj = []
        self.lqb = None  # logical qubit
        # self.parent = []

    def add_adjacent(self, idx):
        self.adj.append(idx)


class pGraph:
    def __init__(self, G, C):
        n = G.shape[0]
        self.leng = n
        self.G = G  # adj matrix
        self.C = C  # cost matrix
        self.data = []
        self.coupling_map = []
        for i in range(n):
            nd = pNode(i)
            for j in range(n):
                if G[i, j] == 1:
                    nd.add_adjacent(j)
                    self.coupling_map.append([i, j])
            self.data.append(nd)

    def __getitem__(self, idx):
        return self.data[idx]

    def __len__(self):
        return self.leng

    def copy(self):
        pgh = pGraph(self.G, self.C)
        for i in range(len(self.data)):
            pgh.data[i].lqb = self.data[i].lqb
        return pgh
