import ForceGraph3D from '3d-force-graph';
// eslint-disable-next-line no-unused-vars
import * as THREE from 'three';
import SpriteText from 'three-spritetext';

export default class RelationChart {

  constructor(mapContainer, data, config) {
    const defaultConfig = {
      linkWidth: 0.5
    };

    // Load data from variable or URL
    if (typeof(data) === 'string') {
      this.Graph = ForceGraph3D()(mapContainer).jsonUrl(data);
    } else {
      this.Graph = ForceGraph3D()(mapContainer).graphData(data);
    }

    // set the config, if no config been passed in, set it to default config
    this.config = config || defaultConfig;
  }

  init () {
    this.Graph.nodeAutoColorBy('group')
      .nodeThreeObject(({ avatar }) => {
        const imgTexture = new THREE.TextureLoader().load(avatar);
        const material = new THREE.SpriteMaterial({ map: imgTexture });
        const sprite = new THREE.Sprite(material);
        sprite.scale.set(12, 12);
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
      .linkWidth(this.config.linkWidth)
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
