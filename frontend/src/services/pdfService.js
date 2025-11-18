import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export const generatePDFReport = async (detectionData, annotatedImageData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/generate-report`, {
      detection_data: detectionData,
      annotated_image: annotatedImageData
    });

    if (response.data.success) {
      // Download the PDF
      const link = document.createElement('a');
      link.href = response.data.pdf_data;
      link.download = response.data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      return true;
    } else {
      throw new Error(response.data.error || 'PDF generation failed');
    }
  } catch (error) {
    console.error('PDF generation error:', error);
    throw new Error(error.response?.data?.error || 'Failed to generate PDF report');
  }
};