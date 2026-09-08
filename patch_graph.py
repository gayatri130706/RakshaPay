with open('static/graph_visualizer.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix 1: Remove the newCount check so it always updates (to catch property changes like blacklisting)
old_fetch = '''    async fetchGraphData() {
        try {
            const res = await fetch("/api/network-graph");
            const data = await res.json();
            const newCount = (data.nodes || []).length;
            if (newCount !== this._lastNodeCount) {
                this._lastNodeCount = newCount;
                this.setupGraph(data.nodes, data.links);
            }
        } catch (e) {'''
new_fetch = '''    async fetchGraphData() {
        try {
            const res = await fetch("/api/network-graph");
            const data = await res.json();
            this.setupGraph(data.nodes, data.links);
        } catch (e) {'''
js = js.replace(old_fetch, new_fetch)

# Fix 2: Re-bind selectedNode and hoveredNode after setupGraph
old_setup = '''        // Spawn animated particles along edges for visual fund flow — PRESERVED'''
new_setup = '''        // Re-bind selected/hovered nodes to new instances so inspector doesn't break
        if (this.selectedNode) {
            this.selectedNode = this.nodes.find(n => n.id === this.selectedNode.id) || null;
            if (this.selectedNode) this.updateInspector(this.selectedNode);
        }
        if (this.hoveredNode) {
            this.hoveredNode = this.nodes.find(n => n.id === this.hoveredNode.id) || null;
        }

        // Spawn animated particles along edges for visual fund flow — PRESERVED'''
js = js.replace(old_setup, new_setup)

with open('static/graph_visualizer.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("graph_visualizer.js fixed")
