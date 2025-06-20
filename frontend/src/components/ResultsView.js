import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Download, CheckCircle, AlertTriangle, FileText, BarChart3, ArrowLeft } from 'lucide-react';
import { CSVLink } from 'react-csv';
import { toast } from 'react-toastify';

import { useAppContext } from '../context/AppContext';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const ResultsCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: 700;
  color: #374151;
`;

const BackButton = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f3f4f6;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  color: #374151;
  font-weight: 500;
  transition: all 0.2s ease;
  
  &:hover {
    background: #e5e7eb;
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
`;

const MetricCard = styled.div`
  background: ${props => props.highlight ? 'linear-gradient(135deg, #10b981, #059669)' : '#f9fafb'};
  color: ${props => props.highlight ? 'white' : '#374151'};
  padding: 1.5rem;
  border-radius: 0.75rem;
  text-align: center;
  border: 1px solid ${props => props.highlight ? 'transparent' : '#e5e7eb'};
`;

const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
`;

const MetricLabel = styled.div`
  font-size: 0.875rem;
  opacity: 0.8;
`;

const AccuracyBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: ${props => props.accuracy >= 99 ? '#10b981' : props.accuracy >= 95 ? '#f59e0b' : '#ef4444'};
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-weight: 600;
  font-size: 0.875rem;
`;

const TableSection = styled.div`
  margin: 2rem 0;
`;

const TableTitle = styled.h3`
  font-size: 1.5rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const TableContainer = styled.div`
  background: white;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  max-height: 400px;
  overflow-y: auto;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const Th = styled.th`
  background: #f9fafb;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
`;

const Td = styled.td`
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;
`;

const DownloadButton = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
  }
`;

const ValidationSection = styled.div`
  margin: 2rem 0;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
`;

const ValidationTitle = styled.h4`
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ValidationItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.5rem 0;
  color: ${props => props.type === 'error' ? '#dc2626' : props.type === 'warning' ? '#f59e0b' : '#059669'};
`;

const ResultsView = () => {
  const navigate = useNavigate();
  const { extractionResults, accuracyMetrics } = useAppContext();
  const [selectedTable, setSelectedTable] = useState(0);

  if (!extractionResults) {
    navigate('/');
    return null;
  }

  const { accuracy_rate, total_tables, total_cells, validation_errors, csv_data, validation_results } = extractionResults;

  const formatCSVData = () => {
    if (!csv_data) return [];
    
    // Parse CSV content into array format for react-csv
    const lines = csv_data.split('\n');
    return lines.map(line => line.split(',').map(cell => cell.replace(/"/g, '')));
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 99) return '#10b981';
    if (accuracy >= 95) return '#f59e0b';
    return '#ef4444';
  };

  const handleDownload = () => {
    toast.success('CSV file downloaded successfully!');
  };

  return (
    <Container>
      <ResultsCard>
        <Header>
          <Title>Extraction Results</Title>
          <BackButton
            onClick={() => navigate('/')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <ArrowLeft />
            New Document
          </BackButton>
        </Header>

        <MetricsGrid>
          <MetricCard highlight>
            <MetricValue>
              <AccuracyBadge accuracy={accuracy_rate * 100}>
                <CheckCircle />
                {(accuracy_rate * 100).toFixed(1)}%
              </AccuracyBadge>
            </MetricValue>
            <MetricLabel>Accuracy Rate</MetricLabel>
          </MetricCard>

          <MetricCard>
            <MetricValue>{total_tables}</MetricValue>
            <MetricLabel>Tables Extracted</MetricLabel>
          </MetricCard>

          <MetricCard>
            <MetricValue>{total_cells}</MetricValue>
            <MetricLabel>Total Cells</MetricLabel>
          </MetricCard>

          <MetricCard>
            <MetricValue>{validation_errors}</MetricValue>
            <MetricLabel>Validation Errors</MetricLabel>
          </MetricCard>
        </MetricsGrid>

        {validation_results && validation_results.length > 0 && (
          <ValidationSection>
            <ValidationTitle>
              <Shield />
              Validation Results
            </ValidationTitle>
            {validation_results.map((result, index) => (
              <div key={index}>
                <strong>Table {index + 1}:</strong>
                {result.errors.map((error, errorIndex) => (
                  <ValidationItem key={errorIndex} type="error">
                    <AlertTriangle />
                    {error}
                  </ValidationItem>
                ))}
                {result.warnings.map((warning, warningIndex) => (
                  <ValidationItem key={warningIndex} type="warning">
                    <AlertTriangle />
                    {warning}
                  </ValidationItem>
                ))}
              </div>
            ))}
          </ValidationSection>
        )}

        {csv_data && (
          <TableSection>
            <TableTitle>
              <FileText />
              Extracted Data Preview
            </TableTitle>
            
            <TableContainer>
              <Table>
                <thead>
                  <tr>
                    {formatCSVData()[0]?.map((header, index) => (
                      <Th key={index}>{header}</Th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {formatCSVData().slice(1, 6).map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {row.map((cell, cellIndex) => (
                        <Td key={cellIndex}>{cell}</Td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </Table>
            </TableContainer>
          </TableSection>
        )}

        <ActionButtons>
          <CSVLink
            data={formatCSVData()}
            filename={`extracted_tables_${new Date().toISOString().split('T')[0]}.csv`}
            onClick={handleDownload}
          >
            <DownloadButton
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Download />
              Download CSV
            </DownloadButton>
          </CSVLink>

          <DownloadButton
            onClick={() => navigate('/analytics')}
            style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <BarChart3 />
            View Analytics
          </DownloadButton>
        </ActionButtons>
      </ResultsCard>
    </Container>
  );
};

export default ResultsView; 