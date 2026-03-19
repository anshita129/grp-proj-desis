import { useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();

  return (
    <div className="navbar">
      <h2>Trading Platform</h2>

      <div 
        style={{ cursor: "pointer" }} 
        onClick={() => navigate("/profile")}
      >
        👤
      </div>
    </div>
  );
}

export default Navbar;