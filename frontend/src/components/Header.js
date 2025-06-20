import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { FileText, BarChart3, Home } from 'lucide-react';

const HeaderContainer = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #4f46e5;
  
  svg {
    width: 32px;
    height: 32px;
  }
`;

const Nav = styled.nav`
  display: flex;
  align-items: center;
  gap: 2rem;
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: ${props => props.active ? '#4f46e5' : '#6b7280'};
  font-weight: ${props => props.active ? '600' : '500'};
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  
  &:hover {
    color: #4f46e5;
    background: rgba(79, 70, 229, 0.1);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

const AccuracyBadge = styled.div`
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: "✓";
    font-weight: bold;
  }
`;

const Header = () => {
  const location = useLocation();
  
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <HeaderContainer>
      <Logo>
        <FileText />
        Document CSV Extractor
      </Logo>
      
      <Nav>
        <NavLink to="/" active={isActive('/')}>
          <Home />
          Upload
        </NavLink>
        
        <NavLink to="/analytics" active={isActive('/analytics')}>
          <BarChart3 />
          Analytics
        </NavLink>
        
        <AccuracyBadge>
          99.5% Accuracy
        </AccuracyBadge>
      </Nav>
    </HeaderContainer>
  );
};

export default Header; 