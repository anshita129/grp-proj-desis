import { useState } from "react";
import Profile from "./Profile";

function Navbar() {
  const [showProfile, setShowProfile] = useState(false);

  return (
    <>
      <div className="navbar">
        <h2>Trading Platform</h2>

        <div
          style={{ cursor: "pointer" }}
          onClick={() => setShowProfile(true)}
        >
          👤
        </div>
      </div>

      {/* 🔥 PROFILE POPUP */}
      <Profile
        show={showProfile}
        onClose={() => setShowProfile(false)}
      />
    </>
  );
}

export default Navbar;