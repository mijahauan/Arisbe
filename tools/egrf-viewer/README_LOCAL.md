# EGRF Viewer - Local Installation Guide

## 🚀 **Quick Start**

The EGRF Viewer is a React-based web application that you can run locally on your machine. Here's how to get it up and running:

## 📋 **Prerequisites**

You'll need the following installed on your system:

1. **Node.js** (version 18 or higher)
   - Download from: https://nodejs.org/
   - Verify installation: `node --version`

2. **npm** (comes with Node.js) or **pnpm** (recommended)
   - For pnpm: `npm install -g pnpm`
   - Verify: `pnpm --version`

## 📦 **Installation Steps**

### Option 1: Download the Complete Package

1. **Extract the EGRF toolkit** to your desired directory
2. **Navigate to the egrf-viewer directory**:
   ```bash
   cd egrf-viewer
   ```

3. **Install dependencies**:
   ```bash
   pnpm install
   # or if using npm:
   npm install
   ```

4. **Start the development server**:
   ```bash
   pnpm run dev
   # or if using npm:
   npm run dev
   ```

5. **Open your browser** and go to:
   ```
   http://localhost:5173
   ```

### Option 2: Manual Setup (if needed)

If you need to set up from scratch:

1. **Create a new React app**:
   ```bash
   npm create vite@latest egrf-viewer -- --template react
   cd egrf-viewer
   ```

2. **Install additional dependencies**:
   ```bash
   npm install @tailwindcss/vite tailwindcss lucide-react
   ```

3. **Copy the source files** from the provided package
4. **Follow steps 3-5 from Option 1**

## 🎯 **Using the EGRF Viewer**

Once running, you can:

### **Load Example Files**
- Click "Simple: Socrates is Mortal" for a basic example
- Click "Complex: Nested Contexts" for an advanced example

### **Upload Custom EGRF Files**
- Click "Upload EGRF File" to load your own `.egrf` or `.json` files
- The viewer will validate and display the graph

### **Export Visualizations**
- Click "Download as SVG" to save the rendered graph
- Use the SVG files in presentations, papers, or documentation

## 📁 **File Structure**

```
egrf-viewer/
├── src/
│   ├── assets/
│   │   ├── simple_example.egrf      # Basic example
│   │   └── complex_example.egrf     # Advanced example
│   ├── components/
│   │   ├── ui/                      # UI components
│   │   └── EGRFViewer.jsx          # Main viewer component
│   ├── App.jsx                      # Main app
│   └── main.jsx                     # Entry point
├── package.json                     # Dependencies
├── vite.config.js                   # Build configuration
└── README.md                        # Project documentation
```

## 🔧 **Configuration**

The application is configured to:
- Run on port 5173 by default
- Accept external connections (for network access)
- Hot-reload when files change during development

## 🛠 **Troubleshooting**

### **Port Already in Use**
If port 5173 is busy, Vite will automatically use the next available port (5174, 5175, etc.)

### **Dependencies Issues**
If you encounter dependency issues:
```bash
rm -rf node_modules package-lock.json
npm install
```

### **Build for Production**
To create a production build:
```bash
pnpm run build
# or
npm run build
```

The built files will be in the `dist/` directory.

## 📚 **Creating Custom EGRF Files**

You can create your own EGRF files by following the JSON schema. See the example files in `src/assets/` for reference structure.

### **Basic EGRF Structure**:
```json
{
  "format": "EGRF",
  "version": "1.0",
  "metadata": {
    "title": "Your Graph Title",
    "description": "Description of your graph"
  },
  "entities": [...],
  "predicates": [...],
  "contexts": [...],
  "canvas": {
    "width": 800,
    "height": 600
  }
}
```

## 🎓 **Educational Use**

This viewer is perfect for:
- **Logic courses**: Visual demonstration of existential graphs
- **Research**: Documentation of complex logical structures
- **Presentations**: Export SVG files for slides and papers
- **Prototyping**: Test different visual layouts

## 🔄 **Next Steps**

Once you have the viewer running locally, you can:
1. Create your own EGRF files for specific logical arguments
2. Use it to visualize and validate logical structures
3. Export graphs for use in academic papers or presentations
4. Provide feedback for future development of the full EG-CL-Manus2 integration

The EGRF format is ready for immediate practical use!

