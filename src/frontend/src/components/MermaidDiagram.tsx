"use client";

import React, { useEffect, useRef } from "react";
import Panzoom from "@panzoom/panzoom"; // Import panzoom
// Note: We won't directly import mermaid - we'll load it dynamically
// import mermaid from "mermaid";

interface MermaidDiagramProps {
  chart: string;
  onNodeClick?: (nodeId: string) => void;
  onPanzoomInit?: (instance: ReturnType<typeof Panzoom> | null) => void;
}

const MermaidDiagram: React.FC<MermaidDiagramProps> = ({
  chart,
  onNodeClick,
  onPanzoomInit,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgContainerRef = useRef<HTMLDivElement>(null); // Ref for the inner div containing SVG
  const mermaidInitialized = useRef(false);
  const panzoomInstance = useRef<ReturnType<typeof Panzoom> | null>(null); // Ref for panzoom instance

  useEffect(() => {
    // We only want to import mermaid on the client side
    const initializeMermaidAndPanzoom = async () => {
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

        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = ""; // Clear previous SVG
          // Destroy previous panzoom instance if it exists
          panzoomInstance.current?.destroy();

          try {
            // Generate unique ID to avoid conflicts
            const id = `mermaid-diagram-${Math.random()
              .toString(36)
              .substring(2, 11)}`;

            // Generate SVG
            const { svg } = await mermaid.render(id, chart);
            svgContainerRef.current.innerHTML = svg; // Place SVG inside the dedicated ref

            // --- Panzoom Initialization ---
            // Use requestAnimationFrame to ensure SVG is in the DOM
            requestAnimationFrame(() => {
              const elem = svgContainerRef.current?.querySelector("svg");
              if (elem && svgContainerRef.current) {
                // Double check refs
                const instance = Panzoom(elem, {
                  maxScale: 5,
                  minScale: 0.1,
                  contain: "outside",
                  canvas: true, // Treat SVG as a canvas for better interaction
                });
                panzoomInstance.current = instance;
                // Call the callback prop with the instance
                onPanzoomInit?.(instance);

                // Add mouse wheel zoom functionality (use container for wider capture)
                svgContainerRef.current.addEventListener("wheel", (event) => {
                  // Prevent page scroll while zooming diagram
                  event.preventDefault();
                  instance.zoomWithWheel(event);
                });

                // Add initial reset/fit view after initialization
                setTimeout(() => instance.reset(), 50);
              } else {
                console.error(
                  "Panzoom init failed: SVG element not found after render."
                );
                // Notify parent that init failed
                onPanzoomInit?.(null);
              }
            });

            // Add click handlers to nodes
            if (onNodeClick) {
              const svgElement = svgContainerRef.current.querySelector("svg");
              if (svgElement) {
                const nodes = svgElement.querySelectorAll(".node");
                nodes.forEach((node) => {
                  // Type assertion for node element
                  const htmlNode = node as HTMLElement;

                  htmlNode.addEventListener("click", (e) => {
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
                  htmlNode.style.cursor = "pointer";
                });
              }
            }
          } catch (error) {
            console.error("Error rendering mermaid chart:", error);
            svgContainerRef.current.innerHTML = `<div class="p-4 text-red-500">Error rendering diagram: ${
              error instanceof Error ? error.message : String(error)
            }</div>`;
          }
        }
      } catch (error) {
        console.error("Error loading mermaid library:", error);
        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = `<div class="p-4 text-red-500">Error loading diagram library</div>`;
        }
      }
    };

    initializeMermaidAndPanzoom();

    // Cleanup function to destroy panzoom on component unmount
    return () => {
      // Cleanup: Notify parent that instance is destroyed
      onPanzoomInit?.(null);
      panzoomInstance.current?.destroy();
    };
  }, [chart, onNodeClick, onPanzoomInit]);

  return (
    <div
      ref={containerRef}
      className="mermaid-diagram-container w-full h-full overflow-hidden border rounded-md"
    >
      {" "}
      {/* Ensure container takes space and hides overflow */}
      <div
        ref={svgContainerRef}
        className="w-full h-full flex justify-center items-center"
      >
        {" "}
        {/* Inner container for SVG */}
        <div className="animate-pulse text-gray-400">Loading diagram...</div>
      </div>
    </div>
  );
};

export default MermaidDiagram;
