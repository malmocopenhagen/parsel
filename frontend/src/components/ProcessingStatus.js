import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, AlertCircle, FileText, Table, Shield, Download } from 'lucide-react';

import { useAppContext } from '../context/AppContext';

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
`;

const ProcessingCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: 700;
  color: #374151;
  margin-bottom: 1rem;
`;

const Subtitle = styled.p`
  font-size: 1.125rem;
  color: #6b7280;
  margin-bottom: 3rem;
`;

const ProgressContainer = styled.div`
  margin: 2rem 0;
`;

const StepContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  margin: 0.5rem 0;
  border-radius: 0.5rem;
  background: ${props => props.completed ? '#f0fdf4' : props.active ? '#eff6ff' : '#f9fafb'};
  border: 2px solid ${props => props.completed ? '#22c55e' : props.active ? '#3b82f6' : '#e5e7eb'};
  transition: all 0.3s ease;
`;

const StepIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => props.completed ? '#22c55e' : props.active ? '#3b82f6' : '#9ca3af'};
  color: white;
  font-size: 1.25rem;
`;

const StepContent = styled.div`
  flex: 1;
  text-align: left;
`;

const StepTitle = styled.div`
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.25rem;
`;

const StepDescription = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin: 1rem 0;
`;

const ProgressFill = styled(motion.div)`
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 4px;
`;

const StatusText = styled.div`
  font-size: 1.125rem;
  color: #374151;
  margin: 2rem 0;
  font-weight: 500;
`;

const ErrorContainer = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #dc2626;
`;

const ProcessingStatus = () => {
  const navigate = useNavigate();
  const { processingStatus, processingProgress, error } = useAppContext();
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      id: 'ocr',
      title: 'OCR Processing',
      description: 'Extracting text using multiple OCR engines',
      icon: <FileText />,
      progress: processingProgress.ocr
    },
    {
      id: 'tableDetection',
      title: 'Table Detection',
      description: 'Identifying table structures and boundaries',
      icon: <Table />,
      progress: processingProgress.tableDetection
    },
    {
      id: 'validation',
      title: 'Data Validation',
      description: 'Validating and cleaning extracted data',
      icon: <Shield />,
      progress: processingProgress.validation
    },
    {
      id: 'csvGeneration',
      title: 'CSV Generation',
      description: 'Creating final CSV output',
      icon: <Download />,
      progress: processingProgress.csvGeneration
    }
  ];

  useEffect(() => {
    // Simulate progress updates
    const interval = setInterval(() => {
      if (processingStatus === 'processing') {
        const totalProgress = Object.values(processingProgress).reduce((sum, val) => sum + val, 0);
        const averageProgress = totalProgress / 4;
        
        if (averageProgress >= 100) {
          clearInterval(interval);
          // Navigate to results after a short delay
          setTimeout(() => {
            navigate('/results');
          }, 1000);
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [processingStatus, processingProgress, navigate]);

  const getStepStatus = (stepIndex) => {
    const stepProgress = steps[stepIndex].progress;
    if (stepProgress >= 100) return 'completed';
    if (stepIndex === currentStep) return 'active';
    return 'pending';
  };

  const totalProgress = Object.values(processingProgress).reduce((sum, val) => sum + val, 0) / 4;

  if (error) {
    return (
      <Container>
        <ProcessingCard>
          <ErrorContainer>
            <AlertCircle />
            <div>
              <strong>Processing Error:</strong> {error}
            </div>
          </ErrorContainer>
          <motion.button
            onClick={() => navigate('/')}
            style={{
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '1rem 2rem',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              marginTop: '1rem'
            }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Try Again
          </motion.button>
        </ProcessingCard>
      </Container>
    );
  }

  return (
    <Container>
      <ProcessingCard>
        <Title>Processing Your Document</Title>
        <Subtitle>
          Our advanced OCR system is extracting tables with high precision
        </Subtitle>

        <ProgressContainer>
          <ProgressBar>
            <ProgressFill
              initial={{ width: 0 }}
              animate={{ width: `${totalProgress}%` }}
              transition={{ duration: 0.5 }}
            />
          </ProgressBar>
          <StatusText>{Math.round(totalProgress)}% Complete</StatusText>
        </ProgressContainer>

        {steps.map((step, index) => {
          const status = getStepStatus(index);
          const isCompleted = status === 'completed';
          const isActive = status === 'active';

          return (
            <StepContainer
              key={step.id}
              completed={isCompleted}
              active={isActive}
            >
              <StepIcon completed={isCompleted} active={isActive}>
                {isCompleted ? <CheckCircle /> : isActive ? <Loader2 className="animate-spin" /> : step.icon}
              </StepIcon>
              <StepContent>
                <StepTitle>{step.title}</StepTitle>
                <StepDescription>{step.description}</StepDescription>
              </StepContent>
              {isActive && (
                <div style={{ color: '#3b82f6', fontSize: '0.875rem' }}>
                  {step.progress}%
                </div>
              )}
            </StepContainer>
          );
        })}

        {totalProgress >= 100 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ marginTop: '2rem' }}
          >
            <StatusText style={{ color: '#22c55e', fontWeight: '600' }}>
              Processing complete! Redirecting to results...
            </StatusText>
          </motion.div>
        )}
      </ProcessingCard>
    </Container>
  );
};

export default ProcessingStatus; 