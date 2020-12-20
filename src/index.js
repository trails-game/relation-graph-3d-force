import ForceGraph3D from '3d-force-graph';
import Three from 'three';
import SpriteText from 'three-spritetext';

export default class RelationChart {

  constructor(myMap) {
    const Graph = ForceGraph3D()
      (myMap)
        .jsonUrl('https://raw.githubusercontent.com/vasturiano/3d-force-graph/master/example/datasets/miserables.json')
        .nodeAutoColorBy('group')
        .nodeThreeObject(node => {
          const sprite = new SpriteText(node.id);
          sprite.material.depthWrite = false; // make sprite background transparent
          sprite.color = node.color;
          sprite.textHeight = 8;
          return sprite;
        });

    // Spread nodes a little wider
    Graph.d3Force('charge').strength(-120);
  }
}

(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory :
    (global = global || self, global.RelationChart = factory);
}(this, RelationChart))
