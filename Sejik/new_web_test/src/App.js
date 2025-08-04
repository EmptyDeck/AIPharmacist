import React from "react";
import Ballpit from "./Ballpit";

function App() {
  return (
    <div style={{ width: "100vw", height: "100vh", background: "#fff" }}>
      <Ballpit followCursor={true} />
    </div>
  );
}

export default App;
