import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar">
      <NavLink to="/" className="navbar-brand">
        <span className="navbar-mark" aria-hidden="true" />
        Darukaa.Earth
      </NavLink>
      {user && (
        <nav className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Dashboard
          </NavLink>
        </nav>
      )}
      {user && (
        <div className="navbar-user">
          <span className="navbar-user-name">{user.name}</span>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Log out
          </button>
        </div>
      )}
    </header>
  );
}
