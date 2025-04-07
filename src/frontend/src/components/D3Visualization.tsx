"use client";

import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { Spinner } from "./ui";

interface NodeData {
  id: string;
  name: string;
  type: string;
  description: string;
  source_section?: string;
  source_page?: number;
  details?: Record<string, any>;
  children?: NodeData[];
  parent?: string;
  _isExpanded?: boolean;
  metrics?: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    [key: string]: number | undefined;
  };
  importance?: number; // 0-100 scale indicating importance in the workflow
  is_novel?: boolean; // Indicates if this is a novel contribution
}

interface LinkData {
  source: string;
  target: string;
  type: string;
  description: string;
}

interface D3VisualizationProps {
  nodes: NodeData[];
  links: LinkData[];
  onNodeClick?: (nodeId: string) => void;
  isProcessing?: boolean;
  width?: number;
  height?: number;
  showMetrics?: boolean; // Option to toggle metrics display
  highlightNovel?: boolean; // Option to highlight novel components
}

const D3Visualization: React.FC<D3VisualizationProps> = ({
  nodes,
  links,
  onNodeClick,
  isProcessing = false,
  width = 800,
  height = 600,
  showMetrics = true,
  highlightNovel = true,
}) => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoveredNode, setHoveredNode] = useState<NodeData | null>(null);
  const [visibleNodes, setVisibleNodes] = useState<NodeData[]>([]);
  const [visibleLinks, setVisibleLinks] = useState<LinkData[]>([]);
  const [nodesMap, setNodesMap] = useState<Map<string, NodeData>>(new Map());

  // Get color for each node type
  const getColorForType = (type: string) => {
    const colors: Record<string, string> = {
      data_collection: "#10B981",
      preprocessing: "#6366F1",
      data_partition: "#F59E0B",
      model: "#EF4444",
      training: "#8B5CF6",
      evaluation: "#EC4899",
      results: "#0EA5E9",
    };

    return colors[type] || "#94A3B8";
  };

  // Process nodes to initialize hierarchy and expansion state
  useEffect(() => {
    if (!nodes.length) return;

    // Create a map of all nodes for quick reference
    const nodeMap = new Map<string, NodeData>();

    // Deep clone nodes to avoid mutating props
    const processedNodes = JSON.parse(JSON.stringify(nodes)) as NodeData[];

    // Set initial expansion state and add to map
    processedNodes.forEach((node) => {
      node._isExpanded = false; // Start collapsed
      nodeMap.set(node.id, node);
    });

    setNodesMap(nodeMap);

    // Determine parent-child relationships
    processedNodes.forEach((node) => {
      if (node.children?.length) {
        node._isExpanded = false; // Initialize as collapsed
      }
    });

    // Calculate visible nodes (top-level and expanded children)
    updateVisibleElements(processedNodes, links);
  }, [nodes, links]);

  // Calculate visible nodes and links based on expansion state
  const updateVisibleElements = (
    allNodes: NodeData[],
    allLinks: LinkData[]
  ) => {
    // Filter to only show top-level nodes and children of expanded nodes
    const visibleNodesList = allNodes.filter(
      (node) =>
        !node.parent || // Top-level node
        (node.parent && nodesMap.get(node.parent)?._isExpanded) // Or child of expanded node
    );

    setVisibleNodes(visibleNodesList);

    // Only show links where both source and target are visible
    const visibleNodeIds = new Set(visibleNodesList.map((n) => n.id));
    const visibleLinksList = allLinks.filter(
      (link) =>
        visibleNodeIds.has(link.source.toString()) &&
        visibleNodeIds.has(link.target.toString())
    );

    setVisibleLinks(visibleLinksList);
  };

  // Toggle node expansion
  const toggleNodeExpansion = (nodeId: string) => {
    const updatedMap = new Map(nodesMap);
    const node = updatedMap.get(nodeId);

    if (node && node.children?.length) {
      node._isExpanded = !node._isExpanded;
      updatedMap.set(nodeId, node);
      setNodesMap(updatedMap);

      // Update visible elements
      const allNodes = Array.from(updatedMap.values());
      updateVisibleElements(allNodes, links);

      // Trigger a redraw
      renderVisualization();
    }
  };

  // Get color for node type, but adjust based on importance if available
  const getNodeColor = (node: NodeData) => {
    const baseColor = getColorForType(node.type);

    // If it's a novel contribution, we might want to make it stand out
    if (highlightNovel && node.is_novel) {
      // Return a gold border or different style later
      return baseColor;
    }

    // If importance is defined, adjust color saturation
    if (node.importance !== undefined) {
      // Higher importance = more saturated
      const d3Color = d3.color(baseColor);
      if (d3Color) {
        // Convert to HSL to adjust saturation
        const hsl = d3.hsl(d3Color);
        // Adjust saturation based on importance (0.3-1.0 range)
        hsl.s = 0.3 + (node.importance / 100) * 0.7;
        return hsl.toString();
      }
    }

    return baseColor;
  };

  // Get node size based on importance or number of children
  const getNodeSize = (node: NodeData) => {
    let size = 20; // Base size

    // If node has children, make it bigger
    if (node.children && node.children.length > 0) {
      size += Math.min(node.children.length * 2, 10);
    }

    // If importance is defined, adjust size
    if (node.importance !== undefined) {
      size += (node.importance / 100) * 10;
    }

    return size;
  };

  // Main rendering function
  const renderVisualization = () => {
    if (
      isProcessing ||
      !visibleNodes.length ||
      !visibleLinks.length ||
      !svgRef.current
    ) {
      return;
    }

    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();

    // Set up the SVG container
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    // Create arrow marker definitions for the links
    svg
      .append("defs")
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("refY", 0)
      .attr("orient", "auto")
      .attr("markerWidth", 8)
      .attr("markerHeight", 8)
      .attr("xoverflow", "visible")
      .append("svg:path")
      .attr("d", "M 0,-5 L 10,0 L 0,5")
      .attr("fill", "#888")
      .style("stroke", "none");

    // Create a force simulation
    const simulation = d3
      .forceSimulation()
      .force(
        "link",
        d3
          .forceLink()
          .id((d: any) => d.id)
          .distance(150)
      )
      .force("charge", d3.forceManyBody().strength(-500))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(60));

    // Process the data for D3
    const nodeMap = new Map(visibleNodes.map((node) => [node.id, node]));
    const processedLinks = visibleLinks
      .map((link) => ({
        ...link,
        source: link.source,
        target: link.target,
      }))
      .filter(
        (link) =>
          nodeMap.has(link.source as string) &&
          nodeMap.has(link.target as string)
      );

    // Add a gradient definition for novel components
    const defs = svg.append("defs");

    defs
      .append("linearGradient")
      .attr("id", "novel-gradient")
      .attr("x1", "0%")
      .attr("x2", "100%")
      .attr("y1", "0%")
      .attr("y2", "100%")
      .selectAll("stop")
      .data([
        { offset: "0%", color: "#FFC107" },
        { offset: "100%", color: "#FF9800" },
      ])
      .enter()
      .append("stop")
      .attr("offset", (d) => d.offset)
      .attr("stop-color", (d) => d.color);

    // Create the link elements with styling based on type
    const link = svg
      .append("g")
      .selectAll("line")
      .data(processedLinks)
      .enter()
      .append("line")
      .attr("stroke", (d) => {
        // Customize link color based on relationship type
        const typeColors: Record<string, string> = {
          uses: "#6366F1",
          inputs_to: "#10B981",
          outputs_to: "#EF4444",
          evaluated_by: "#8B5CF6",
          compared_to: "#F59E0B",
        };
        return typeColors[d.type] || "#888";
      })
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.6)
      .attr("marker-end", "url(#arrowhead)")
      .attr("class", (d) => `link ${d.type}`);

    // Create a group for each node
    const nodeGroup = svg
      .append("g")
      .selectAll(".node-group")
      .data(visibleNodes)
      .enter()
      .append("g")
      .attr("class", "node-group")
      .call(
        d3
          .drag<SVGGElement, NodeData>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      )
      .on("click", (event, d) => {
        event.stopPropagation();
        if (onNodeClick) {
          onNodeClick(d.id);
        }
      })
      .on("dblclick", (event, d) => {
        // Double click to expand/collapse
        event.stopPropagation();
        toggleNodeExpansion(d.id);
      })
      .on("mouseover", (event, d) => {
        setHoveredNode(d);
      })
      .on("mouseout", () => {
        setHoveredNode(null);
      });

    // Add the main circle for each node with dynamic size and styling
    nodeGroup
      .append("circle")
      .attr("r", getNodeSize)
      .attr("fill", (d) => getNodeColor(d))
      .attr("stroke", (d) => {
        // Special border for novel components
        if (highlightNovel && d.is_novel) {
          return "#FFC107"; // Gold border for novel components
        }
        return d3.color(getNodeColor(d))?.darker().toString() || "#000";
      })
      .attr("stroke-width", (d) => (highlightNovel && d.is_novel ? 3 : 2))
      .attr("stroke-dasharray", (d) =>
        highlightNovel && d.is_novel ? "3,2" : "none"
      );

    // Add metrics badge if metrics exist and showMetrics is true
    nodeGroup
      .filter(
        (d) => showMetrics && d.metrics && Object.keys(d.metrics).length > 0
      )
      .append("circle")
      .attr("r", 8)
      .attr("cx", -15)
      .attr("cy", -15)
      .attr("fill", "#3B82F6")
      .attr("stroke", "#2563EB")
      .attr("stroke-width", 1)
      .attr("class", "metrics-indicator");

    // Add a value to the metrics badge (highest metric value)
    nodeGroup
      .filter(
        (d) => showMetrics && d.metrics && Object.keys(d.metrics).length > 0
      )
      .append("text")
      .attr("x", -15)
      .attr("y", -15)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-size", "8px")
      .attr("font-weight", "bold")
      .attr("fill", "white")
      .text((d) => {
        // Find the highest metric value
        if (!d.metrics) return "";
        const highestValue = Math.max(
          ...(Object.values(d.metrics).filter(
            (v) => v !== undefined
          ) as number[])
        );
        // Format to at most 2 decimal places
        return highestValue.toFixed(highestValue >= 10 ? 0 : 1);
      });

    // Add star icon for novel components
    nodeGroup
      .filter((d) => highlightNovel && d.is_novel)
      .append("text")
      .attr("x", 0)
      .attr("y", -22)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-size", "14px")
      .attr("fill", "#FFC107")
      .attr("stroke", "#F59E0B")
      .attr("stroke-width", 0.5)
      .text("★"); // Unicode star symbol

    // Add expand/collapse indicator if node has children
    nodeGroup
      .filter((d) => d.children && d.children.length > 0)
      .append("circle")
      .attr("r", 8)
      .attr("cx", 15)
      .attr("cy", 15)
      .attr("fill", "white")
      .attr("stroke", "#333")
      .attr("stroke-width", 1)
      .attr("class", "expand-collapse-indicator");

    // Add +/- symbol to indicator
    nodeGroup
      .filter((d) => d.children && d.children.length > 0)
      .append("text")
      .attr("x", 15)
      .attr("y", 15)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text((d) => (d._isExpanded ? "−" : "+"));

    // Add text for each node
    nodeGroup
      .append("text")
      .attr("dy", 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .text((d) =>
        d.name.length > 20 ? d.name.substring(0, 20) + "..." : d.name
      )
      .attr("fill", "#111");

    // Update the simulation with the nodes and links
    simulation.nodes(visibleNodes).on("tick", ticked);
    simulation
      .force<d3.ForceLink<NodeData, LinkData>>("link")
      ?.links(processedLinks);

    // Function to handle position updates on each tick
    function ticked() {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      nodeGroup.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    }

    // Drag event handlers
    function dragstarted(
      event: d3.D3DragEvent<SVGGElement, NodeData, NodeData>
    ) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, NodeData, NodeData>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, NodeData, NodeData>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Return cleanup function
    return () => {
      simulation.stop();
    };
  };

  // Call renderVisualization whenever visibleNodes or visibleLinks change
  useEffect(() => {
    renderVisualization();
  }, [visibleNodes, visibleLinks, width, height, isProcessing]);

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center p-4 h-full">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-600">
          Processing paper and generating visualization...
        </p>
      </div>
    );
  }

  if (!nodes || nodes.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No components to visualize
      </div>
    );
  }

  return (
    <div className="relative">
      <svg ref={svgRef} className="w-full border rounded-md"></svg>
      {hoveredNode && (
        <div className="absolute top-0 right-0 bg-white p-3 shadow-lg rounded-md text-sm max-w-xs">
          <div className="flex items-center justify-between">
            <h4 className="font-bold">{hoveredNode.name}</h4>
            {hoveredNode.is_novel && (
              <span className="ml-2 px-1 py-0.5 text-xs bg-amber-100 text-amber-800 rounded-full">
                Novel
              </span>
            )}
          </div>
          <p className="text-gray-600 text-xs">{hoveredNode.type}</p>
          <p className="mt-1">{hoveredNode.description}</p>

          {/* Show metrics if available */}
          {hoveredNode.metrics &&
            Object.keys(hoveredNode.metrics).length > 0 && (
              <div className="mt-2 text-xs">
                <h5 className="font-medium text-gray-700">Metrics:</h5>
                <ul className="mt-1 space-y-1">
                  {Object.entries(hoveredNode.metrics).map(
                    ([key, value]) =>
                      value !== undefined && (
                        <li key={key} className="flex justify-between">
                          <span>{key.replace(/_/g, " ")}:</span>
                          <span className="font-medium">
                            {value.toFixed(2)}
                          </span>
                        </li>
                      )
                  )}
                </ul>
              </div>
            )}

          {/* Show importance if available */}
          {hoveredNode.importance !== undefined && (
            <div className="mt-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-700">Importance:</span>
                <span
                  className={`font-medium ${
                    hoveredNode.importance > 75
                      ? "text-green-600"
                      : hoveredNode.importance > 50
                      ? "text-blue-600"
                      : hoveredNode.importance > 25
                      ? "text-amber-600"
                      : "text-gray-600"
                  }`}
                >
                  {hoveredNode.importance}/100
                </span>
              </div>
            </div>
          )}

          {hoveredNode.children && hoveredNode.children.length > 0 && (
            <p className="mt-1 text-xs text-blue-600">
              {hoveredNode._isExpanded
                ? `Double-click to collapse (${hoveredNode.children.length} children)`
                : `Double-click to expand (${hoveredNode.children.length} children)`}
            </p>
          )}
        </div>
      )}

      <div className="absolute bottom-2 left-2 bg-white p-2 shadow-md rounded-md text-xs space-y-1">
        <p className="font-medium">
          Tip: Double-click on a node with children to expand/collapse
        </p>
        <div className="flex items-center space-x-2">
          <span className="inline-block w-3 h-3 rounded-full bg-amber-400 border border-amber-600"></span>
          <span>Novel component</span>
        </div>
        {showMetrics && (
          <div className="flex items-center space-x-2">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Performance metric</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default D3Visualization;
