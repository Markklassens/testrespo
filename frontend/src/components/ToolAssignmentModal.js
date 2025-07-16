import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  XMarkIcon, 
  UserIcon, 
  CubeIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { assignToolToAdmin, unassignToolFromAdmin } from '../store/slices/toolsSlice';
import { fetchUsers } from '../store/slices/usersSlice';
import LoadingSpinner from './LoadingSpinner';

const ToolAssignmentModal = ({ isOpen, onClose, tool, onSuccess }) => {
  const dispatch = useDispatch();
  const { users, loading: usersLoading } = useSelector(state => state.users);
  const { assignments } = useSelector(state => state.tools);
  const [selectedAdmin, setSelectedAdmin] = useState('');
  const [isAssigning, setIsAssigning] = useState(false);

  useEffect(() => {
    if (isOpen) {
      dispatch(fetchUsers({ role: 'admin' }));
      // Set current assigned admin if exists
      if (tool?.assigned_admin_id) {
        setSelectedAdmin(tool.assigned_admin_id);
      } else {
        setSelectedAdmin('');
      }
    }
  }, [isOpen, tool, dispatch]);

  const handleAssign = async () => {
    if (!selectedAdmin) {
      toast.error('Please select an admin');
      return;
    }

    setIsAssigning(true);
    try {
      await dispatch(assignToolToAdmin({ 
        toolId: tool.id, 
        adminId: selectedAdmin 
      })).unwrap();
      toast.success('Tool assigned successfully');
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(error || 'Failed to assign tool');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleUnassign = async () => {
    setIsAssigning(true);
    try {
      await dispatch(unassignToolFromAdmin(tool.id)).unwrap();
      toast.success('Tool unassigned successfully');
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(error || 'Failed to unassign tool');
    } finally {
      setIsAssigning(false);
    }
  };

  if (!isOpen) return null;

  // Filter admins only
  const adminUsers = users.filter(user => user.user_type === 'admin' || user.user_type === 'superadmin');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Tool Assignment
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Tool Info */}
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mr-3">
                <CubeIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">
                  {tool?.name}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {tool?.short_description}
                </p>
              </div>
            </div>
          </div>

          {/* Current Assignment Status */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Current Status
            </h4>
            <div className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              {tool?.assigned_admin_id ? (
                <div className="flex items-center">
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Assigned to: {
                      adminUsers.find(u => u.id === tool.assigned_admin_id)?.full_name || 
                      'Unknown Admin'
                    }
                  </span>
                </div>
              ) : (
                <div className="flex items-center">
                  <ExclamationCircleIcon className="h-5 w-5 text-yellow-500 mr-2" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Not assigned to any admin
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Admin Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Assign to Admin
            </label>
            {usersLoading ? (
              <div className="flex justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : (
              <select
                value={selectedAdmin}
                onChange={(e) => setSelectedAdmin(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">Select an admin...</option>
                {adminUsers.map(admin => (
                  <option key={admin.id} value={admin.id}>
                    {admin.full_name} ({admin.email}) - {admin.user_type}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              disabled={isAssigning}
              className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 disabled:opacity-50"
            >
              Cancel
            </button>
            
            {tool?.assigned_admin_id && (
              <button
                onClick={handleUnassign}
                disabled={isAssigning}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isAssigning ? (
                  <LoadingSpinner size="sm" className="mr-2" />
                ) : null}
                Unassign
              </button>
            )}
            
            <button
              onClick={handleAssign}
              disabled={isAssigning || !selectedAdmin}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isAssigning ? (
                <LoadingSpinner size="sm" className="mr-2" />
              ) : null}
              {tool?.assigned_admin_id ? 'Reassign' : 'Assign'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolAssignmentModal;