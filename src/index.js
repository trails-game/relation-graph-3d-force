import ForceGraph3D from '3d-force-graph';
import * as THREE from 'three';
import SpriteText from 'three-spritetext';
// eslint-disable-next-line no-unused-vars
import $ from "jquery";

export default class RelationChart {

  constructor(mapContainer, data, config) {
    const defaultConfig = {
      linkWidth: 0.5,
      nodeSize: 5
    };

    // Load data from variable or URL
    if (typeof(data) === 'string') {
      this.Graph = ForceGraph3D()(mapContainer).jsonUrl(data);
    } else {
      this.buildNeighbours(data);
    }

    this.Graph = ForceGraph3D()(mapContainer).graphData(data);
    // set the config, if no config been passed in, set it to default config
    this.config = config || defaultConfig;

    this.highlightNodes = new Set();
    this.highlightLinks = new Set();
    this.hoverNode = null;

    this.nodes = [];
    this.links = [];
  }

  buildNeighbours(data) {
    return data.links.forEach(link => {
      const a = data.nodes[link.source];
      const b = data.nodes[link.target];
      !a.neighbors && (a.neighbors = []);
      !b.neighbors && (b.neighbors = []);
      a.neighbors.push(b);
      b.neighbors.push(a);

      !a.links && (a.links = []);
      !b.links && (b.links = []);
      a.links.push(link);
      b.links.push(link);
    });
  }

  updateHighlight() {
    // trigger update of highlighted objects in scene
    this.nodes.forEach(node => {
      if (this.hoverNode && !this.highlightNodes.has(node)) {
        node.__threeObj.material.opacity = 0.1;
      } else {
        node.__threeObj.material.opacity = 1;
      }
    });

    this.Graph
      .linkWidth(this.Graph.linkWidth())
      //.nodeThreeObject(this.Graph.nodeThreeObject())
      .linkDirectionalParticles(this.Graph.linkDirectionalParticles());
  }

  init () {
    this.Graph.nodeThreeObject((node) => {
        this.nodes.push(node);

        const textureLoader = new THREE.TextureLoader();

  			const imgTexture = textureLoader.load( node.avatar, function ( texture ) {
  				texture.encoding = THREE.sRGBEncoding;
  				texture.mapping = THREE.EquirectangularReflectionMapping;
  			} );

        var circle = new THREE.Mesh(
          new THREE.CircleGeometry( this.config.nodeSize, 32 ),
          new THREE.MeshBasicMaterial({
            map: imgTexture,
            side: THREE.DoubleSide
          })
        );

        circle.material.transparent = true;
        if (this.hoverNode && !this.highlightNodes.has(node)) {
          circle.material.opacity = 0.1;
        }
        return circle;
      })
      .onNodeHover(node => {
        // no state change
        if ((!node && !this.highlightNodes.size) || (node && this.hoverNode === node)) return;

        this.highlightNodes.clear();
        this.highlightLinks.clear();
        if (node) {
          this.highlightNodes.add(node);
          node.neighbors.forEach(neighbor => this.highlightNodes.add(neighbor));
          node.links.forEach(link => this.highlightLinks.add(link));
        }

        this.hoverNode = node || null;
        this.updateHighlight();
      })
      .linkThreeObjectExtend(true)
      .linkThreeObject(link => {
        this.links.push(link);
        // extend link with text sprite
        const sprite = new SpriteText(link.relation);
        sprite.color = 'lightgrey';
        sprite.textHeight = 1.5;
        return sprite;
      })
      .linkWidth(link => this.highlightLinks.has(link) ? 1 : 0)
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
