"use client";

import React, {
  useEffect,
  useRef,
  useCallback,
  useState,
  forwardRef,
  useImperativeHandle,
} from "react";
import Panzoom from "@panzoom/panzoom"; // Import panzoom
// Note: We won't directly import mermaid - we'll load it dynamically
// import mermaid from "mermaid";

interface MermaidDiagramProps {
  chart: string;
  onNodeClick?: (nodeId: string) => void;
  onPanzoomInit?: (instance: ReturnType<typeof Panzoom> | null) => void;
}

// Define handle types for useImperativeHandle
export interface MermaidDiagramHandle {
  zoomIn: () => void;
  zoomOut: () => void;
  reset: () => void;
}

const MermaidDiagram = forwardRef<MermaidDiagramHandle, MermaidDiagramProps>(
  ({ chart, onNodeClick, onPanzoomInit }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const svgContainerRef = useRef<HTMLDivElement>(null); // Ref for the inner div containing SVG
    const mermaidInitialized = useRef(false);
    const panzoomInstance = useRef<ReturnType<typeof Panzoom> | null>(null); // Ref for panzoom instance
    const [renderError, setRenderError] = useState<string | null>(null);
    const pendingWheelEventsRef = useRef<WheelEvent[]>([]);
    const wheelProcessingRef = useRef(false);
    const lastWheelEventRef = useRef<number | null>(null);

    // Process wheel events in a controlled way
    const processWheelQueue = useCallback(() => {
      if (
        wheelProcessingRef.current ||
        pendingWheelEventsRef.current.length === 0
      ) {
        return;
      }

      wheelProcessingRef.current = true;
      const event = pendingWheelEventsRef.current.shift();

      if (event && panzoomInstance.current) {
        try {
          // Get current scale for smoother zoom effect
          const currentScale = panzoomInstance.current.getScale();

          // Calculate zoom factor based on wheel delta
          // Use a smaller factor for smoother zoom
          const wheelDelta = event.deltaY || event.detail || 0;
          const zoomFactor = 1 - wheelDelta * 0.001; // Smaller value = smoother zoom

          // Apply new scale directly with animation
          const newScale = currentScale * zoomFactor;

          // Get current mouse position
          const containerRect =
            svgContainerRef.current?.getBoundingClientRect() || null;

          // If we have container dimensions, zoom toward the cursor position
          if (containerRect) {
            const offsetX = event.clientX - containerRect.left;
            const offsetY = event.clientY - containerRect.top;

            panzoomInstance.current.zoomToPoint(newScale, offsetX, offsetY, {
              animate: true,
              duration: 150, // Keep animation short for wheel zooming
            });
          } else {
            // Fallback to regular zoom if we can't get container position
            panzoomInstance.current.zoom(newScale, {
              animate: true,
              duration: 150,
            });
          }
        } catch (error) {
          console.error("Error during wheel zoom:", error);
        }
      }

      // Small delay between zoom operations to prevent flashing
      setTimeout(() => {
        wheelProcessingRef.current = false;
        if (pendingWheelEventsRef.current.length > 0) {
          processWheelQueue();
        }
      }, 20); // Small delay for smoother zooming
    }, []);

    // Safe function to center and fit content
    const resetView = useCallback(() => {
      console.log(
        "[MermaidDiagram] resetView called. Has panzoomInstance?",
        !!panzoomInstance.current
      );
      if (!panzoomInstance.current || !svgContainerRef.current) return;

      try {
        const svg = svgContainerRef.current.querySelector("svg");
        if (!svg) return;

        // Reset to scale 1 first
        panzoomInstance.current.zoom(1);
        panzoomInstance.current.pan(0, 0);

        // Then calculate fit based on container and content sizes
        const svgBounds = svg.getBoundingClientRect();
        const containerBounds = svgContainerRef.current.getBoundingClientRect();

        if (svgBounds.width === 0 || svgBounds.height === 0) return;

        // Calculate scale to fit
        const scaleX = containerBounds.width / svgBounds.width;
        const scaleY = containerBounds.height / svgBounds.height;
        const scale = Math.min(scaleX, scaleY, 1) * 0.95;

        // Center the content
        const centerX = (containerBounds.width - svgBounds.width * scale) / 2;
        const centerY = (containerBounds.height - svgBounds.height * scale) / 2;

        // Apply transforms in sequence with a small delay
        setTimeout(() => {
          if (panzoomInstance.current) {
            panzoomInstance.current.zoom(scale);
            panzoomInstance.current.pan(centerX, centerY);
          }
        }, 50);
      } catch (error) {
        console.error("Error resetting view:", error);
      }
    }, []);

    // Custom zoom methods with clear visual feedback
    const zoomIn = useCallback(() => {
      console.log(
        "[MermaidDiagram] zoomIn called. Has panzoomInstance?",
        !!panzoomInstance.current
      );
      if (!panzoomInstance.current) return;

      try {
        // Get current scale and increase by a fixed percentage (30%)
        const currentScale = panzoomInstance.current.getScale();
        const newScale = currentScale * 1.3; // Stronger zoom effect

        // Apply the new scale with animation for smooth visual feedback
        panzoomInstance.current.zoom(newScale, {
          animate: true,
          duration: 300, // Longer animation for more visible effect
          easing: "ease-out",
        });
      } catch (error) {
        console.error("Error during zoomIn:", error);
      }
    }, []);

    const zoomOut = useCallback(() => {
      console.log(
        "[MermaidDiagram] zoomOut called. Has panzoomInstance?",
        !!panzoomInstance.current
      );
      if (!panzoomInstance.current) return;

      try {
        // Get current scale and decrease by a fixed percentage
        const currentScale = panzoomInstance.current.getScale();
        const newScale = currentScale * 0.75; // Decrease scale by 25%

        // Apply the new scale with animation for smooth visual feedback
        panzoomInstance.current.zoom(newScale, {
          animate: true,
          duration: 300, // Longer animation for more visible effect
          easing: "ease-out",
        });
      } catch (error) {
        console.error("Error during zoomOut:", error);
      }
    }, []);

    // Set up click handlers for diagram nodes
    const setupNodeClickHandlers = useCallback(
      (svg: SVGElement) => {
        if (!svg || !onNodeClick) return;

        try {
          const nodes = svg.querySelectorAll(".node");
          nodes.forEach((node) => {
            const htmlNode = node as HTMLElement;
            htmlNode.style.cursor = "pointer";

            htmlNode.addEventListener("click", () => {
              const textElement = node.querySelector("text");
              if (textElement) {
                const text = textElement.textContent || "";
                const nodeId = text.replace(/^\[|\]$/g, "");
                onNodeClick(nodeId);
              }
            });
          });
        } catch (error) {
          console.error("Error setting up node click handlers:", error);
        }
      },
      [onNodeClick]
    );

    // Initialize Panzoom on the SVG container
    const initializePanzoom = useCallback(
      (wrapper: HTMLElement) => {
        if (!wrapper) {
          console.error(
            "[MermaidDiagram] InitializePanzoom called with null wrapper"
          );
          return;
        }
        console.log("[MermaidDiagram] Initializing Panzoom...");
        try {
          const svg = wrapper.querySelector("svg");
          if (!svg || !(svg instanceof SVGElement)) {
            console.error(
              "[MermaidDiagram] No valid SVG element found for Panzoom"
            );
            onPanzoomInit?.(null); // Notify parent of failure
            return;
          }
          console.log("[MermaidDiagram] SVG element found:", svg);

          // Set SVG to take full size of container
          svg.style.width = "100%";
          svg.style.height = "100%";
          svg.style.maxHeight = "100%";
          svg.style.maxWidth = "100%";

          // Create stable Panzoom instance
          console.log("[MermaidDiagram] Creating Panzoom instance...");
          const instance = Panzoom(wrapper, {
            maxScale: 6,
            minScale: 0.1,
            startScale: 0.9,
            startX: 0,
            startY: 0,
            canvas: true,
            step: 0.05,
            animate: true,
            duration: 250,
            easing: "ease-out",
            cursor: "grab",
            // Add safety checks
            beforeMouseDown: () => {
              // Allow panning even if SVG is slightly out of sync briefly
              return true;
            },
            // Customize zoom behavior
            setTransform: (
              elem: HTMLElement | SVGElement,
              { x, y, scale }: { x: number; y: number; scale: number }
            ) => {
              // Apply transforms with CSS transform for better performance
              wrapper.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;

              // Change cursor to 'grabbing' while actively panning/zooming
              wrapper.style.cursor = "grabbing";

              // Add a subtle shadow effect when zoomed in
              if (scale > 1.0) {
                const shadowIntensity = Math.min(20, (scale - 1) * 15);
                elem.style.filter = `drop-shadow(0 0 ${shadowIntensity}px rgba(0, 0, 0, 0.2))`;
              } else {
                elem.style.filter = "none";
              }
            },
          });
          console.log("[MermaidDiagram] Panzoom instance created:", instance);

          // Store instance and notify parent
          panzoomInstance.current = instance;
          console.log(
            "[MermaidDiagram] panzoomInstance.current set:",
            !!panzoomInstance.current
          );
          onPanzoomInit?.(instance);

          // Add wheel handler with event throttling
          const wheelHandler = (event: WheelEvent) => {
            event.preventDefault();

            // Ignore fast repeated events for stability
            const now = Date.now();
            if (
              lastWheelEventRef.current &&
              now - lastWheelEventRef.current < 20
            ) {
              return;
            }
            lastWheelEventRef.current = now;

            // Add to queue and process if not already processing
            pendingWheelEventsRef.current.push(event);
            if (
              pendingWheelEventsRef.current.length === 1 &&
              !wheelProcessingRef.current
            ) {
              processWheelQueue();
            }

            // Add log inside to check instance
            if (!panzoomInstance.current) {
              console.warn(
                "[MermaidDiagram] Wheel event ignored: panzoomInstance is null."
              );
              return;
            }
          };

          wrapper.addEventListener("wheel", wheelHandler, { passive: false });
          console.log("[MermaidDiagram] Wheel listener added.");

          // Set up click handlers for nodes
          setupNodeClickHandlers(svg);

          // Reset view to fit content
          console.log("[MermaidDiagram] Scheduling initial resetView...");
          setTimeout(resetView, 200);

          // Add touch gesture support for mobile/tablet devices
          let initialDistance = 0;
          let initialScale = 1;

          const touchStartHandler = (event: TouchEvent) => {
            if (event.touches.length === 2) {
              event.preventDefault();
              initialDistance = Math.hypot(
                event.touches[0].clientX - event.touches[1].clientX,
                event.touches[0].clientY - event.touches[1].clientY
              );
              initialScale = panzoomInstance.current?.getScale() || 1;
            }
          };

          const touchMoveHandler = (event: TouchEvent) => {
            if (event.touches.length === 2 && panzoomInstance.current) {
              event.preventDefault();
              const currentDistance = Math.hypot(
                event.touches[0].clientX - event.touches[1].clientX,
                event.touches[0].clientY - event.touches[1].clientY
              );
              const ratio = currentDistance / initialDistance;
              const newScale = initialScale * ratio;

              // Find center point between two touches
              const centerX =
                (event.touches[0].clientX + event.touches[1].clientX) / 2;
              const centerY =
                (event.touches[0].clientY + event.touches[1].clientY) / 2;

              const containerRect =
                svgContainerRef.current?.getBoundingClientRect();
              if (containerRect) {
                const offsetX = centerX - containerRect.left;
                const offsetY = centerY - containerRect.top;

                panzoomInstance.current.zoomToPoint(
                  newScale,
                  offsetX,
                  offsetY,
                  {
                    animate: false,
                  }
                );
              } else {
                panzoomInstance.current.zoom(newScale, { animate: false });
              }
            }
          };

          wrapper.addEventListener("touchstart", touchStartHandler, {
            passive: false,
          });
          wrapper.addEventListener("touchmove", touchMoveHandler, {
            passive: false,
          });
          console.log("[MermaidDiagram] Touch listeners added.");

          // Reset cursor when pan/zoom ends
          wrapper.addEventListener("panzoomend", () => {
            wrapper.style.cursor = "grab";
          });
        } catch (error) {
          console.error("Error initializing Panzoom:", error);
          panzoomInstance.current = null; // Ensure instance is null on error
          onPanzoomInit?.(null);
        }
      },
      [onPanzoomInit, processWheelQueue, resetView, setupNodeClickHandlers]
    );

    // Initialize Mermaid and render diagram
    const renderMermaidDiagram = useCallback(async () => {
      if (!svgContainerRef.current) return;

      try {
        // Clear previous content
        svgContainerRef.current.innerHTML =
          '<div class="animate-pulse text-gray-400">Rendering diagram...</div>';
        setRenderError(null);

        // Clean up existing Panzoom instance
        if (panzoomInstance.current) {
          try {
            panzoomInstance.current.destroy();
          } catch {
            /* Ignore cleanup errors */
          }
          panzoomInstance.current = null;
        }

        // Dynamically import Mermaid
        const mermaidModule = await import("mermaid");
        const mermaid = mermaidModule.default;

        // Initialize Mermaid once
        if (!mermaidInitialized.current) {
          mermaid.initialize({
            startOnLoad: false,
            theme: "neutral",
            securityLevel: "loose",
            fontFamily: "system-ui, -apple-system, sans-serif",
          });
          mermaidInitialized.current = true;
        }

        // Generate unique ID for rendering
        const id = `mermaid-${Date.now()}-${Math.random()
          .toString(36)
          .substring(2, 9)}`;

        // Create a wrapper for the rendered SVG
        const wrapper = document.createElement("div");
        wrapper.className =
          "mermaid-wrapper w-full h-full flex justify-center items-center relative";

        // Render the diagram
        const { svg } = await mermaid.render(id, chart);
        wrapper.innerHTML = svg;

        // Replace container content with the wrapper
        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = "";
          svgContainerRef.current.appendChild(wrapper);

          // Delay Panzoom initialization to ensure DOM is stable
          setTimeout(() => {
            initializePanzoom(wrapper);
          }, 150);
        }
      } catch (error) {
        console.error("Error rendering Mermaid diagram:", error);
        setRenderError(
          error instanceof Error ? error.message : "Failed to render diagram"
        );

        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = `
          <div class="p-4 text-red-500 flex flex-col items-center justify-center">
            <div class="font-semibold mb-2">Error rendering diagram</div>
            <div class="text-sm">${
              error instanceof Error ? error.message : "Unknown error"
            }</div>
          </div>
        `;
        }

        onPanzoomInit?.(null);
      }
    }, [chart, onPanzoomInit, initializePanzoom]);

    // Render diagram when chart changes
    useEffect(() => {
      renderMermaidDiagram();

      // Cleanup on unmount or chart change
      return () => {
        if (panzoomInstance.current) {
          try {
            panzoomInstance.current.destroy();
          } catch (error) {
            console.error("Error destroying panzoom instance:", error);
          }
          panzoomInstance.current = null;
        }

        // Clear any pending wheel events
        pendingWheelEventsRef.current = [];
        wheelProcessingRef.current = false;

        // Notify parent
        onPanzoomInit?.(null);
      };
    }, [chart, renderMermaidDiagram, onPanzoomInit]);

    // Expose methods via useImperativeHandle
    useImperativeHandle(
      ref,
      () => ({
        zoomIn,
        zoomOut,
        reset: resetView,
      }),
      [zoomIn, zoomOut, resetView]
    );

    return (
      <div
        ref={containerRef}
        className="mermaid-diagram-container relative w-full h-full overflow-hidden border rounded-md"
      >
        <div
          ref={svgContainerRef}
          className="w-full h-full flex justify-center items-center bg-white"
        >
          <div className="animate-pulse text-gray-400">Loading diagram...</div>
        </div>

        {renderError && (
          <div className="absolute bottom-4 left-4 bg-red-100 text-red-700 p-2 rounded-md text-xs">
            {renderError}
          </div>
        )}
      </div>
    );
  }
);

MermaidDiagram.displayName = "MermaidDiagram"; // Add display name for DevTools

export default MermaidDiagram;
