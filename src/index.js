import ForceGraph3D from '3d-force-graph';
// eslint-disable-next-line no-unused-vars
import Three from 'three';
import SpriteText from 'three-spritetext';

export default class RelationChart {

  constructor(mapContainer, data) {
    if (typeof(data) === 'string') {
      this.Graph = ForceGraph3D()(mapContainer).jsonUrl(data);
    } else {
      this.Graph = ForceGraph3D()(mapContainer).graphData(data);
    }
  }

  init () {
    this.Graph.nodeAutoColorBy('group')
      .nodeThreeObject(node => {
        const sprite = new SpriteText(node.id);
        sprite.material.depthWrite = false; // make sprite background transparent
        sprite.color = node.color;
        sprite.textHeight = 8;
        return sprite;
      })
      .linkThreeObjectExtend(true)
      .linkThreeObject(link => {
        // extend link with text sprite
        const sprite = new SpriteText(`${link.source} > ${link.target}`);
        sprite.color = 'lightgrey';
        sprite.textHeight = 1.5;
        return sprite;
      })
      .linkPositionUpdate((sprite, { start, end }) => {
        const middlePos = Object.assign(...['x', 'y', 'z'].map(c => ({
          [c]: start[c] + (end[c] - start[c]) / 2 // calc middle point
        })));

        // Position sprite
        Object.assign(sprite.position, middlePos);
      });

    // Spread nodes a little wider
    this.Graph.d3Force('charge').strength(-120);
  }
}

(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory :
    (global = global || self, global.RelationChart = factory);
}(this, RelationChart))
