'use strict';

import ForceGraph3D from '3d-force-graph';
import * as THREE from 'three';
import SpriteText from 'three-spritetext';
import axios from 'axios';

export default class RelationChart {

  constructor(mapContainer, data, customConfig) {
    this.mapContainer = mapContainer;
    this.data = data
    this.config = {
      linkWidth: 0.5,
      linkTextSize: 1.5,
      linkTextColor: 'lightgrey',
      nodeSize: 5,
      nodeTextSize: 5,
      particleWidth: 1,
      particleDensity: 5,
      orgColor: 'red',
      characterColor: 'skyblue'
    };

    // custom config will overwrite default config
    if (customConfig) {
      Object.assign(this.config, customConfig);
    }

    this.highlightNodes = new Set();
    this.highlightLinks = new Set();
    this.particleLinks = new Set();
    this.hoverNode = null;
    this.clickedNode = null;

    this.nodes = [];
    this.links = [];
  }

  async loadData(data) {
    if (typeof data === 'string'){
      try{
        const response = await axios.get(data);
        this.data = response.data;
      } catch (err) {
        console.log(err);
        this.data = null;
      }
    } else {
      this.data = data;
    }
  }

  buildNeighboursAndTestPos(data) {
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

      // Generate random 1 decimal number between 0.3 and 0.7
      link.textPos = (Math.floor(Math.random() * 5) + 3) / 10;
    });
  }

  async init() {
    // Load data from variable or URL
    await this.loadData(this.data);
    if (!this.data){
      throw "Empty Data"
    }

    this.buildNeighboursAndTestPos(this.data);
    this.Graph = ForceGraph3D()(this.mapContainer).graphData(this.data);

    // Set the size of the map to equal div
    this.Graph.width(this.mapContainer.offsetWidth);
    // 80 is the size of the webpage header
    this.Graph.height(this.mapContainer.offsetHeight - 80);
  }

  updateHighlight() {
    // trigger update of highlighted objects in scene

    this.nodes.forEach(node => {
      /*
      if (this.hoverNode && this.highlightNodes.has(node)) {
        node.__threeObj.material.opacity = 1;
      } else {
        node.__threeObj.material.opacity = 0.6;
      }
      */
      if (this.hoverNode && !this.highlightNodes.has(node)) {
        node.__threeObj.material.opacity = 0.1;
      } else if (!this.hoverNode) {
        node.__threeObj.material.opacity = 0.6;
      } else {
        node.__threeObj.material.opacity = 1;
      }
    });

    this.links.forEach(link => {
      if (this.hoverNode && !this.highlightLinks.has(link)) {
        link.__lineObj.visible = false;
        link.__arrowObj.visible = false;
      } else {
        link.__lineObj.visible = true;
        link.__arrowObj.visible = true;
      }

    });

    this.Graph.linkDirectionalParticles(this.Graph.linkDirectionalParticles());
    /*
    this.Graph
      .linkWidth(this.Graph.linkWidth())
      //.nodeThreeObject(this.Graph.nodeThreeObject())
      .linkDirectionalParticles(this.Graph.linkDirectionalParticles());
      */
  }

  async render() {
    await this.init();

    this.Graph.nodeThreeObject((node) => {
        this.nodes.push(node);
        let obj;
        if (node.avatar) {

          // load img from URL
          const textureLoader = new THREE.TextureLoader();
          const imgTexture = textureLoader.load( node.avatar, function ( texture ) {
            texture.encoding = THREE.sRGBEncoding;
            texture.mapping = THREE.EquirectangularReflectionMapping;
          });

          // Mesh a circle with previous img material
          let circle = new THREE.Mesh(
            new THREE.CircleGeometry( this.config.nodeSize, 32 ),
            new THREE.MeshBasicMaterial({
              map: imgTexture,
              side: THREE.DoubleSide
            })
          );

          circle.material.transparent = true;
          circle.material.opacity = 0.6;

          // Make object always facing camera
          // eslint-disable-next-line no-unused-vars
          circle.onBeforeRender = (renderer, scene, camera, geometry, material, group) => {
            circle.quaternion.copy(camera.quaternion);
          }
          obj = circle;
        } else {
          const sprite = new SpriteText(node.name);
          sprite.material.depthWrite = false; // make sprite background transparent
          sprite.color = node.isOrganization ?
                           this.config.orgColor : this.config.characterColor;
          sprite.textHeight = this.config.nodeTextSize;
          obj = sprite;
        }

        return obj;
      })
      .onNodeHover(node => {
        // If a node is been clicked, hover on it or its neighbours should emit particles
        if (this.clickedNode) {
          if (node && node !== this.clickedNode) {
            // hover on its neighbours
            node.links.forEach((link) => {
              if ((link.source === node && link.target === this.clickedNode) ||
                  (link.target === node && link.source === this.clickedNode)) {
                    this.particleLinks.add(link);
              }
            });
          } else if (node && node === this.clickedNode) {
            // hover on itself
            this.clickedNode.links.forEach(link => this.particleLinks.add(link));
          } else {
            this.particleLinks.clear();
          }
          this.Graph.linkDirectionalParticles(this.Graph.linkDirectionalParticles());
          return;
        }

        // no state change
        if ((!node && !this.highlightNodes.size) || (node && this.hoverNode === node));

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
      .onNodeClick(node => {
        // All click actions are preceeded hover actions
        if (this.clickedNode === node) {
          // Clicked on the node that has been clicked
          this.clickedNode = null;
          this.hoverNode = null;
          this.highlightNodes.clear();
          this.highlightLinks.clear();
          this.particleLinks.clear();
          this.updateHighlight();
        } else if (this.clickedNode) {
          // Clicked on a different node than current clickedNode
          this.clickedNode = node;
          this.hoverNode = node;
          this.highlightNodes.clear();
          this.highlightLinks.clear();
          this.highlightNodes.add(node);
          node.neighbors.forEach(neighbor => this.highlightNodes.add(neighbor));
          node.links.forEach(link => {
            this.highlightLinks.add(link);
            this.particleLinks.add(link)
          });
          this.updateHighlight();
        } else {
          // No node is in clicked status
          this.clickedNode = node;
          node.links.forEach(link => this.particleLinks.add(link));
          this.Graph.linkDirectionalParticles(this.Graph.linkDirectionalParticles());
        }
      })
      // TODO: add proper URL
      // eslint-disable-next-line no-unused-vars
      .onNodeRightClick(node => {
        // On desktop devices, right click to open new tab for character
        let win = window.open("https://trails-game.com/character/juna-crawford/", '_blank');
        win.focus();
      })
      .onBackgroundClick(() => {
        // Cancel clickedNode status
        this.highlightNodes.clear();
        this.highlightLinks.clear();
        this.clickedNode = null;
        this.hoverNode = null;
        this.updateHighlight();
      })
      .linkDirectionalParticles(link => this.particleLinks.has(link) ?
                                          this.config.particleDensity : 0)
      .linkDirectionalParticleWidth(this.config.particleWidth)
      .linkThreeObjectExtend(true)
      .linkThreeObject(link => {
        this.links.push(link);
        // console.log(link);
        // extend link with text sprite
        const sprite = new SpriteText(link.relation);
        sprite.color = this.config.linkTextColor;
        sprite.textHeight = this.config.linkTextSize;
        return sprite;
      })
      .linkDirectionalArrowLength(2)
      .linkDirectionalArrowRelPos(1)
      .linkCurvature(0.2)
      .linkAutoColorBy('type')
      // .linkWidth(0.2)
      //.linkWidth(link => this.highlightLinks.has(link) ? 1 : 0)
      //.linkVisibility(link => this.highlightLinks.has(link) ? false : true)
      // eslint-disable-next-line no-unused-vars
      .linkPositionUpdate((sprite, { start, end }, link) => {
        /*
        const middlePos = Object.assign(...['x', 'y', 'z'].map(c => ({
          [c]: start[c] + (end[c] - start[c]) / 2 // calc middle point
        })));
        */
        // Position sprite
        // Object.assign(sprite.position, middlePos);
        // console.log(link.__curve.getPoint(0.5));
        Object.assign(sprite.position, link.__curve.getPoint(link.textPos));
      });

    // Spread nodes a little wider
    this.Graph.d3Force('charge').strength(-120);
  }
}

(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory :
    (global = global || self, global.RelationChart = factory);
}(this, RelationChart))
