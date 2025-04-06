"use client";

import React, { useEffect, useRef } from "react";
// Note: We won't directly import mermaid - we'll load it dynamically
// import mermaid from "mermaid";

interface MermaidDiagramProps {
  chart: string;
  onNodeClick?: (nodeId: string) => void;
}

const MermaidDiagram: React.FC<MermaidDiagramProps> = ({
  chart,
  onNodeClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mermaidInitialized = useRef(false);

  useEffect(() => {
    // We only want to import mermaid on the client side
    const initializeMermaid = async () => {
      try {
        // Dynamically import mermaid
        const mermaid = (await import("mermaid")).default;

        // Only initialize once
        if (!mermaidInitialized.current) {
          mermaid.initialize({
            startOnLoad: false,
            theme: "neutral",
            securityLevel: "loose",
            fontFamily: "system-ui, -apple-system, sans-serif",
          });
          mermaidInitialized.current = true;
        }

        if (containerRef.current) {
          containerRef.current.innerHTML = "";

          try {
            // Generate unique ID to avoid conflicts
            const id = `mermaid-diagram-${Math.random()
              .toString(36)
              .substring(2, 11)}`;

            // Generate SVG
            const { svg } = await mermaid.render(id, chart);
            containerRef.current.innerHTML = svg;

            // Add click handlers to nodes
            if (onNodeClick) {
              const svgElement = containerRef.current.querySelector("svg");
              if (svgElement) {
                const nodes = svgElement.querySelectorAll(".node");
                nodes.forEach((node) => {
                  node.addEventListener("click", (e) => {
                    // Extract node ID from the text content
                    const textElement = node.querySelector("text");
                    if (textElement) {
                      // Extract the text without brackets
                      const text = textElement.textContent || "";
                      const nodeId = text.replace(/^\[|\]$/g, "");
                      onNodeClick(nodeId);
                    }
                  });

                  // Make nodes look clickable
                  node.style.cursor = "pointer";
                });
              }
            }
          } catch (error) {
            console.error("Error rendering mermaid chart:", error);
            containerRef.current.innerHTML = `<div class="p-4 text-red-500">Error rendering diagram: ${
              error instanceof Error ? error.message : String(error)
            }</div>`;
          }
        }
      } catch (error) {
        console.error("Error loading mermaid library:", error);
        if (containerRef.current) {
          containerRef.current.innerHTML = `<div class="p-4 text-red-500">Error loading diagram library</div>`;
        }
      }
    };

    initializeMermaid();
  }, [chart, onNodeClick]);

  return (
    <div className="mermaid-diagram-container">
      <div ref={containerRef} className="text-center overflow-auto p-4">
        <div className="animate-pulse text-gray-400">Loading diagram...</div>
      </div>
    </div>
  );
};

export default MermaidDiagram;
