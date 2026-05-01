# Technical Specification Report: Optimized ILIB Hardware

## 1. Delivery Modalities
*   **Invasive Fiber-Optic**: Direct delivery, high efficiency, requires sterile biocompatible quartz fibers.
*   **Transcutaneous (VPBM)**: Skin-surface delivery, lower efficiency, requires higher power (60-250mW) and strict thermal management.

## 2. Critical Specifications
*   **Wavelength Purity**: $\le 5\text{nm}$ (Targeting CCO absorption peaks).
*   **Power Stability**: $\pm 5\%$ over 60 mins (Requires TEC and PID closed-loop).
*   **Thermal Limit**: $\le 40^\circ\text{C}$ for blood; $\le 42^\circ\text{C}$ for skin.

## 3. Ideal Device Blueprint
*   **Source**: AlGaInP Laser Diode / He-Ne.
*   **Wavelength**: 632.8nm (Invasive) / 660nm (Transcutaneous) $\pm 2\text{nm}$.
*   **Safety**: Emergency stop, Contact sensors (for transcutaneous), Gamma-sterilized single-use catheters (for invasive).
