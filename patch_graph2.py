import re

with open('static/graph_visualizer.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix 1: Remove newCount check
js = re.sub(r'const newCount = \(data\.nodes \|\| \[\]\)\.length;\s*if \(newCount !== this\._lastNodeCount\) \{\s*this\._lastNodeCount = newCount;\s*this\.setupGraph\(data\.nodes, data\.links\);\s*\}', 'this.setupGraph(data.nodes, data.links);', js)

# Fix 2: Re-bind selectedNode
target = 'this.particles = [];'
replacement = '''if (this.selectedNode) {
            this.selectedNode = this.nodes.find(n => n.id === this.selectedNode.id) || null;
            if (this.selectedNode) this.updateInspector(this.selectedNode);
        }
        if (this.hoveredNode) {
            this.hoveredNode = this.nodes.find(n => n.id === this.hoveredNode.id) || null;
        }

        this.particles = [];'''
js = js.replace(target, replacement)

with open('static/graph_visualizer.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Graph fixed")
