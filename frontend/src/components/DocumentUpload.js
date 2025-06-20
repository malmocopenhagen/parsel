import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import axios from 'axios';

import { useAppContext } from '../context/AppContext';

// API base URL - will use Railway URL in production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const HeroSection = styled.div`
  text-align: center;
  margin-bottom: 3rem;
`;

const Title = styled.h1`
  font-size: 3rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const Subtitle = styled.p`
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
`;

const UploadSection = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
`;

const Dropzone = styled.div`
  border: 3px dashed ${props => props.isDragActive ? '#4f46e5' : '#d1d5db'};
  border-radius: 1rem;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: ${props => props.isDragActive ? 'rgba(79, 70, 229, 0.05)' : 'transparent'};
  
  &:hover {
    border-color: #4f46e5;
    background: rgba(79, 70, 229, 0.05);
  }
`;

const UploadIcon = styled.div`
  font-size: 4rem;
  color: #4f46e5;
  margin-bottom: 1rem;
`;

const UploadText = styled.div`
  font-size: 1.25rem;
  color: #374151;
  margin-bottom: 0.5rem;
`;

const UploadSubtext = styled.div`
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 2rem;
`;

const FileInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f3f4f6;
  border-radius: 0.5rem;
  margin-top: 1rem;
`;

const FileIcon = styled.div`
  color: #4f46e5;
`;

const FileDetails = styled.div`
  flex: 1;
`;

const FileName = styled.div`
  font-weight: 600;
  color: #374151;
`;

const FileSize = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`;

const ProcessButton = styled(motion.button)`
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 2rem;
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
`;

const FeatureCard = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  color: white;
`;

const FeatureIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #fbbf24;
`;

const FeatureTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
`;

const FeatureDescription = styled.p`
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
`;

const DocumentUpload = () => {
  const navigate = useNavigate();
  const { dispatch } = useAppContext();
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      dispatch({ type: 'SET_UPLOADED_FILE', payload: file });
    }
  }, [dispatch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const handleProcess = async () => {
    if (!uploadedFile) return;

    setIsProcessing(true);
    dispatch({ type: 'SET_PROCESSING_STATUS', payload: 'uploading' });

    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const uploadResponse = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (uploadResponse.data.filepath) {
        dispatch({ type: 'SET_PROCESSING_STATUS', payload: 'processing' });
        navigate('/processing');

        // Start extraction
        const extractionResponse = await axios.post(`${API_BASE_URL}/extract`, {
          filepath: uploadResponse.data.filepath,
          options: {
            enable_preview: true,
            confidence_threshold: 0.7
          }
        });

        if (extractionResponse.data.success) {
          dispatch({ type: 'SET_EXTRACTION_RESULTS', payload: extractionResponse.data });
          dispatch({ type: 'SET_ACCURACY_METRICS', payload: {
            accuracy_rate: extractionResponse.data.accuracy_rate,
            total_cells: extractionResponse.data.total_cells,
            validation_errors: extractionResponse.data.validation_errors
          }});
          navigate('/results');
        } else {
          throw new Error(extractionResponse.data.error || 'Extraction failed');
        }
      }
    } catch (error) {
      console.error('Processing error:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      toast.error(`Processing failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container>
      <HeroSection>
        <Title>Extract Tables with 99.5% Accuracy</Title>
        <Subtitle>
          Upload your scanned documents and let our advanced OCR technology extract 
          tables into clean, accurate CSV files with industry-leading precision.
        </Subtitle>
      </HeroSection>

      <UploadSection>
        <Dropzone {...getRootProps()} isDragActive={isDragActive}>
          <input {...getInputProps()} />
          <UploadIcon>
            {isDragActive ? <CheckCircle /> : <Upload />}
          </UploadIcon>
          <UploadText>
            {isDragActive ? 'Drop your file here' : 'Drag & drop your document here'}
          </UploadText>
          <UploadSubtext>
            or click to browse files (PDF, PNG, JPG, TIFF, BMP up to 50MB)
          </UploadSubtext>
        </Dropzone>

        {uploadedFile && (
          <FileInfo>
            <FileIcon>
              <FileText />
            </FileIcon>
            <FileDetails>
              <FileName>{uploadedFile.name}</FileName>
              <FileSize>{formatFileSize(uploadedFile.size)}</FileSize>
            </FileDetails>
          </FileInfo>
        )}

        <ProcessButton
          onClick={handleProcess}
          disabled={!uploadedFile || isProcessing}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {isProcessing ? 'Processing...' : 'Extract to CSV'}
        </ProcessButton>
      </UploadSection>

      <FeaturesGrid>
        <FeatureCard>
          <FeatureIcon>🎯</FeatureIcon>
          <FeatureTitle>High Accuracy</FeatureTitle>
          <FeatureDescription>
            Achieve 99.5% accuracy with our multi-engine OCR system and advanced validation algorithms.
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureIcon>⚡</FeatureIcon>
          <FeatureTitle>Fast Processing</FeatureTitle>
          <FeatureDescription>
            Process large documents with multiple pages and tables in seconds, not minutes.
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureIcon>🔍</FeatureIcon>
          <FeatureTitle>Smart Detection</FeatureTitle>
          <FeatureDescription>
            Automatically detect table structures, headers, and data types for optimal extraction.
          </FeatureDescription>
        </FeatureCard>

        <FeatureCard>
          <FeatureIcon>📊</FeatureIcon>
          <FeatureTitle>Clean Output</FeatureTitle>
          <FeatureDescription>
            Generate properly formatted CSV files with clean headers and validated data.
          </FeatureDescription>
        </FeatureCard>
      </FeaturesGrid>
    </Container>
  );
};

export default DocumentUpload; 