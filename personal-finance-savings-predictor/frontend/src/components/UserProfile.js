import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function UserProfile({ userId }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    age: '',
    dependents: 0,
    occupation: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const API_URL = 'http://localhost:5000/api';

  // Occupation options
  const occupations = ['Salaried', 'Business', 'Freelancer', 'Student', 'Retired'];

  useEffect(() => {
    // Fetch user profile if it exists
    const fetchUserProfile = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/profile/${userId}`);
        
        // Update form with existing profile data
        setFormData({
          age: response.data.age,
          dependents: response.data.dependents,
          occupation: response.data.occupation
        });
        
        setLoading(false);
      } catch (err) {
        // If profile doesn't exist (404) that's okay, we'll create a new one
        if (err.response && err.response.status === 404) {
          setLoading(false);
        } else {
          setError('Failed to fetch profile data. Please try again later.');
          setLoading(false);
          console.error('Error fetching profile:', err);
        }
      }
    };

    fetchUserProfile();
  }, [userId, API_URL]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'age' || name === 'dependents' ? parseInt(value, 10) || '' : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      // Validate form data
      if (!formData.age || !formData.occupation) {
        throw new Error('Please fill in all required fields');
      }

      if (formData.age < 18 || formData.age > 100) {
        throw new Error('Age must be between 18 and 100');
      }

      if (formData.dependents < 0) {
        throw new Error('Number of dependents cannot be negative');
      }

      // Submit profile to the API
      await axios.post(`${API_URL}/profile`, {
        user_id: userId,
        age: formData.age,
        dependents: formData.dependents,
        occupation: formData.occupation
      });

      setSuccess(true);
      
      // Redirect to dashboard after short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to update profile. Please try again.');
      console.error('Error updating profile:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading">Loading profile data...</div>;

  return (
    <div className="profile-container">
      <h1>{formData.age ? 'Update Your Profile' : 'Create Your Profile'}</h1>
      
      <p className="profile-info">
        Your demographic information helps our system provide more accurate savings predictions.
        This information is only used for analysis and is not shared with any third parties.
      </p>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Profile updated successfully!</div>}
      
      <form onSubmit={handleSubmit} className="profile-form">
        <div className="form-group">
          <label htmlFor="age">Age:</label>
          <input
            type="number"
            id="age"
            name="age"
            value={formData.age}
            onChange={handleChange}
            placeholder="Enter your age"
            min="18"
            max="100"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="dependents">Number of Dependents:</label>
          <input
            type="number"
            id="dependents"
            name="dependents"
            value={formData.dependents}
            onChange={handleChange}
            placeholder="How many people do you support?"
            min="0"
            required
          />
          <small>Include spouse, children, parents, or others you financially support</small>
        </div>
        
        <div className="form-group">
          <label htmlFor="occupation">Occupation:</label>
          <select
            id="occupation"
            name="occupation"
            value={formData.occupation}
            onChange={handleChange}
            required
          >
            <option value="">Select your occupation</option>
            {occupations.map((occupation) => (
              <option key={occupation} value={occupation}>{occupation}</option>
            ))}
          </select>
        </div>
        
        <button 
          type="submit" 
          className="submit-btn" 
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </form>
      
      <div className="data-privacy">
        <h3>Data Privacy Note</h3>
        <p>
          The information you provide is used only for generating personalized savings predictions.
          Your data is stored securely and is not shared with third parties.
          You can delete your profile at any time.
        </p>
      </div>
    </div>
  );
}

export default UserProfile;