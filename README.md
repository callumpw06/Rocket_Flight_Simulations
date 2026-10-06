# Supersonic Aerodynamics Workflow: OpenRocket to OpenFOAM

This guide outlines the standard procedure for running high-fidelity, parallel computational fluid dynamics (CFD) simulations on liquid-fuelled rocket airframes. Designed to validate supersonic flight trajectories and aerodynamic heating for high-altitude desert launches, this workflow covers the entire pipeline: exporting geometry from OpenRocket, prepping the CAD in FreeCAD, and executing a Spalart-Allmaras turbulence model in OpenFOAM.

## Prerequisites
*   **OpenRocket** (for initial airframe design)
*   **FreeCAD** (for mesh preparation)
*   **OpenFOAM v12+** (compiled with MPI for parallel processing)
*   **ParaView** (for post-processing and visualization)

---

## 1. Geometry Export (OpenRocket)
1. Open your finalized rocket design in OpenRocket.
2. Navigate to **File > Export > Wavefront OBJ** (or directly to STL if supported by your version).
3. Ensure you are exporting the external airframe only. Internal components (recovery systems, bulkheads) will unnecessarily complicate the external aerodynamic mesh.

## 2. Geometry Preparation (FreeCAD)
OpenFOAM requires a water-tight, single-surface `.stl` file oriented correctly within the wind tunnel coordinate system.
1. Import your OpenRocket export into FreeCAD.
2. **Align the Axes:** Rotate the rocket so the nosecone points directly along the **+Z axis**. This ensures the geometry perfectly aligns with standard vertical wind tunnel configurations and the `(0 0 -Z)` velocity vectors in OpenFOAM.
3. **Fuse the Geometry:** If the rocket imported as multiple parts (nosecone, body tube, fins), use the Part workbench to apply a **Boolean Union** to fuse them into a single solid object.
4. **Export to STL:** Select the fused solid and export it as an `.stl` file. 
5. **Rename the Patch:** Open the `.stl` file in a text editor. Change the name on the first line (e.g., `solid ASCII`) to your desired patch name (e.g., `solid mysteryMachine`). Do the same for the last line (`endsolid mysteryMachine`). Save the file and place it in your OpenFOAM case's `constant/triSurface/` directory.

---

## 3. Mesh Generation (OpenFOAM)
Supersonic simulations require high-resolution boundary layers to capture oblique shockwaves and turbulent wakes. We execute the meshing pipeline on a **single core** first to ensure the rocket patch is permanently written to the master directory, avoiding MPI reconstruction data loss.

1. **Clean the Case:** Remove any broken meshes or old processor folders.
   ```bash
   foamCleanCase
   rm -rf processor*
   ```
2. **Generate the Wind Tunnel:** Build the background blockMesh.
   ```bash
   blockMesh
   ```
3. **Extract Leading Edges:** Generate the `.eMesh` file to ensure the fin edges remain razor-sharp for accurate shockwave separation.
   ```bash
   surfaceFeatureExtract
   ```
4. **Snap the Geometry:** Run the mesher on a single core to lock the rocket into the master `constant/polyMesh` directory.
   ```bash
   snappyHexMesh -overwrite
   ```
5. **Verify the Mesh:** Confirm the mesh successfully carved out the airframe before proceeding.
   ```bash
   grep -A 5 "mysteryMachine" constant/polyMesh/boundary
   ```

---

## 4. Boundary Physics Configuration
Before splitting the mesh for parallel execution, the new solid wall (the rocket) must be defined in the initial physics directories to support the Spalart-Allmaras turbulence model.

Navigate to the `0/` directory and add the rocket patch to the following files:

*   **`0/U` (Velocity):** Enforce friction at the wall.
    ```text
    mysteryMachine { type noSlip; }
    ```
*   **`0/p`, `0/T`, `0/e`, `0/nuTilda` (Scalars):** Set the hull as adiabatic (no heat/pressure leaks).
    ```text
    mysteryMachine { type zeroGradient; }
    ```
*   **`0/nut` (Turbulence):** Apply the specific wall function required by Spalart-Allmaras.
    ```text
    mysteryMachine { type nutUSpaldingWallFunction; value uniform 0; }
    ```

---

## 5. Parallel Execution
With the mesh locked and the boundary layer physics defined, distribute the workload across the CPU cores and launch the solver.

1. **Decompose the Mesh:** Slice the domain for your processors (ensure `numberOfSubdomains` in `system/decomposeParDict` matches your core count).
   ```bash
   decomposePar
   ```
2. **Launch the Solver:** Execute the transonic/supersonic solver. The `tee` command will write the output to a log file while keeping it visible in the terminal.
   ```bash
   mpirun -np 4 foamRun -parallel | tee log.foamRun
   ```
3. **Resuming a Simulation:** If you need to stop and restart, change `startFrom` in `system/controlDict` to `latestTime`, then run:
   ```bash
   mpirun -np 4 foamRun -parallel | tee -a log.foamRun
   ```

---

## 6. Visualization & Post-Processing (ParaView)
1. Open the case in ParaView.
   ```bash
   paraview view.foam &
   ```
2. In the Properties panel, change the **Case Type** to **Decomposed Case** so ParaView reads directly from the processor folders.
3. Scroll to the **Mesh Regions** list. Uncheck `internalMesh` and check your rocket patch to view the physical airframe.
4. To view the turbulent friction gripping the hull, change the color variable to `nut`.
5. To view the shockwaves, re-enable `internalMesh`, create a **Slice** down the center of the rocket, and color by `p` (Pressure) or generate a **Mach** field. Clamp the color scale slightly above atmospheric pressure to filter out the extreme nosecone stagnation and reveal the weaker oblique waves off the fins.