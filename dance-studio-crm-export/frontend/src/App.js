import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "./components/ui/card";
import { Calendar } from "./components/ui/calendar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { toast } from "sonner";
import { format, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay, parseISO } from "date-fns";
import { CalendarIcon, Users, BookOpen, Clock, Plus, UserPlus } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext(null);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      toast.error('Login failed. Please check your credentials.');
      return false;
    }
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API}/auth/register`, userData);
      toast.success('Registration successful! Please login.');
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      toast.error('Registration failed. Please try again.');
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Component
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'owner',
    studio_name: ''
  });
  const { login, register, token } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (token) {
      navigate('/', { replace: true });
    }
  }, [token, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = isLogin ? 
      await login(formData.email, formData.password) :
      await register(formData);
    
    if (success && isLogin) {
      // Redirect to dashboard on successful login
      navigate('/', { replace: true });
    } else if (success && !isLogin) {
      setIsLogin(true);
      setFormData({ ...formData, password: '' });
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">
            {isLogin ? 'Welcome Back' : 'Create Account'}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {isLogin ? 'Sign in to your studio account' : 'Set up your dance studio management'}
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <Input
                  name="name"
                  type="text"
                  placeholder="Full Name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
                <Input
                  name="studio_name"
                  type="text"
                  placeholder="Studio Name (optional)"
                  value={formData.studio_name}
                  onChange={handleInputChange}
                />
                <Select name="role" value={formData.role} onValueChange={(value) => setFormData({...formData, role: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="owner">Studio Owner</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                    <SelectItem value="teacher">Teacher</SelectItem>
                  </SelectContent>
                </Select>
              </>
            )}
            
            <Input
              name="email"
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleInputChange}
              required
            />
            <Input
              name="password"
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleInputChange}
              required
            />
            
            <Button type="submit" className="w-full">
              {isLogin ? 'Sign In' : 'Create Account'}
            </Button>
          </form>
          
          <div className="mt-4 text-center">
            <button
              type="button"
              className="text-sm text-primary hover:underline"
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Dashboard Stats Component
const DashboardStats = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API}/dashboard/stats`);
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };
    fetchStats();
  }, []);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold">{stats.total_classes}</p>
              <p className="text-sm text-muted-foreground">Total Classes</p>
            </div>
            <BookOpen className="h-8 w-8 text-primary" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold">{stats.total_teachers}</p>
              <p className="text-sm text-muted-foreground">Teachers</p>
            </div>
            <Users className="h-8 w-8 text-primary" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold">{stats.classes_today}</p>
              <p className="text-sm text-muted-foreground">Classes Today</p>
            </div>
            <Clock className="h-8 w-8 text-primary" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Weekly Calendar Component
const WeeklyCalendar = ({ selectedDate, onDateSelect }) => {
  const [classes, setClasses] = useState([]);
  
  useEffect(() => {
    fetchWeeklyClasses();
  }, [selectedDate]);

  const fetchWeeklyClasses = async () => {
    try {
      const startDate = startOfWeek(selectedDate, { weekStartsOn: 1 }).toISOString();
      const response = await axios.get(`${API}/calendar/weekly?start_date=${startDate}`);
      setClasses(response.data);
    } catch (error) {
      console.error('Failed to fetch classes:', error);
    }
  };

  const weekStart = startOfWeek(selectedDate, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(selectedDate, { weekStartsOn: 1 });
  const weekDays = eachDayOfInterval({ start: weekStart, end: weekEnd });

  const getClassesForDay = (day) => {
    return classes.filter(cls => 
      isSameDay(parseISO(cls.start_datetime), day)
    );
  };

  const getClassTypeColor = (classType) => {
    const colors = {
      ballet: 'bg-pink-100 text-pink-800',
      hip_hop: 'bg-purple-100 text-purple-800',
      jazz: 'bg-yellow-100 text-yellow-800',
      contemporary: 'bg-blue-100 text-blue-800',
      tap: 'bg-green-100 text-green-800',
      salsa: 'bg-red-100 text-red-800',
      ballroom: 'bg-indigo-100 text-indigo-800'
    };
    return colors[classType] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg border">
      <div className="grid grid-cols-7 border-b">
        {weekDays.map(day => (
          <div key={day.toISOString()} className="p-4 text-center border-r last:border-r-0">
            <div className="text-sm font-medium text-muted-foreground mb-1">
              {format(day, 'EEE')}
            </div>
            <div className="text-lg font-semibold">
              {format(day, 'd')}
            </div>
          </div>
        ))}
      </div>
      
      <div className="grid grid-cols-7 min-h-96">
        {weekDays.map(day => {
          const dayClasses = getClassesForDay(day);
          return (
            <div key={day.toISOString()} className="p-2 border-r last:border-r-0 space-y-1">
              {dayClasses.map(cls => (
                <div
                  key={cls.id}
                  className="text-xs p-2 rounded cursor-pointer hover:opacity-80 transition-opacity"
                >
                  <Badge className={`w-full justify-start ${getClassTypeColor(cls.class_type)}`}>
                    <div className="flex flex-col text-left w-full">
                      <div className="font-medium">{cls.title}</div>
                      <div className="text-xs">{format(parseISO(cls.start_datetime), 'HH:mm')}</div>
                      <div className="text-xs">{cls.teacher_name}</div>
                    </div>
                  </Badge>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Add Class Dialog
const AddClassDialog = ({ onClassAdded }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [teachers, setTeachers] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    class_type: '',
    teacher_id: '',
    start_datetime: '',
    end_datetime: '',
    capacity: 20,
    description: '',
    studio_room: '',
    price: 0
  });

  useEffect(() => {
    fetchTeachers();
  }, []);

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${API}/teachers`);
      setTeachers(response.data);
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/classes`, {
        ...formData,
        start_datetime: new Date(formData.start_datetime).toISOString(),
        end_datetime: new Date(formData.end_datetime).toISOString()
      });
      toast.success('Class created successfully!');
      setIsOpen(false);
      onClassAdded();
      setFormData({
        title: '',
        class_type: '',
        teacher_id: '',
        start_datetime: '',
        end_datetime: '',
        capacity: 20,
        description: '',
        studio_room: '',
        price: 0
      });
    } catch (error) {
      console.error('Failed to create class:', error);
      toast.error('Failed to create class');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Class
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Schedule New Class</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            placeholder="Class Title"
            value={formData.title}
            onChange={(e) => setFormData({...formData, title: e.target.value})}
            required
          />
          
          <Select value={formData.class_type} onValueChange={(value) => setFormData({...formData, class_type: value})}>
            <SelectTrigger>
              <SelectValue placeholder="Class Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ballet">Ballet</SelectItem>
              <SelectItem value="hip_hop">Hip Hop</SelectItem>
              <SelectItem value="jazz">Jazz</SelectItem>
              <SelectItem value="contemporary">Contemporary</SelectItem>
              <SelectItem value="tap">Tap</SelectItem>
              <SelectItem value="salsa">Salsa</SelectItem>
              <SelectItem value="ballroom">Ballroom</SelectItem>
            </SelectContent>
          </Select>

          <Select value={formData.teacher_id} onValueChange={(value) => setFormData({...formData, teacher_id: value})}>
            <SelectTrigger>
              <SelectValue placeholder="Select Teacher" />
            </SelectTrigger>
            <SelectContent>
              {teachers.map(teacher => (
                <SelectItem key={teacher.id} value={teacher.id}>
                  {teacher.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Start Time</label>
              <Input
                type="datetime-local"
                value={formData.start_datetime}
                onChange={(e) => setFormData({...formData, start_datetime: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">End Time</label>
              <Input
                type="datetime-local"
                value={formData.end_datetime}
                onChange={(e) => setFormData({...formData, end_datetime: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              type="number"
              placeholder="Capacity"
              value={formData.capacity}
              onChange={(e) => setFormData({...formData, capacity: parseInt(e.target.value)})}
            />
            <Input
              placeholder="Studio Room"
              value={formData.studio_room}
              onChange={(e) => setFormData({...formData, studio_room: e.target.value})}
            />
          </div>

          <Button type="submit" className="w-full">Schedule Class</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Add Teacher Dialog
const AddTeacherDialog = ({ onTeacherAdded }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    specialties: [],
    bio: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/teachers`, formData);
      toast.success('Teacher added successfully!');
      setIsOpen(false);
      onTeacherAdded();
      setFormData({
        name: '',
        email: '',
        phone: '',
        specialties: [],
        bio: ''
      });
    } catch (error) {
      console.error('Failed to add teacher:', error);
      toast.error('Failed to add teacher');
    }
  };

  const toggleSpecialty = (specialty) => {
    const newSpecialties = formData.specialties.includes(specialty)
      ? formData.specialties.filter(s => s !== specialty)
      : [...formData.specialties, specialty];
    setFormData({...formData, specialties: newSpecialties});
  };

  const specialties = ['ballet', 'hip_hop', 'jazz', 'contemporary', 'tap', 'salsa', 'ballroom'];

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <UserPlus className="w-4 h-4 mr-2" />
          Add Teacher
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add New Teacher</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            placeholder="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
          
          <Input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />

          <Input
            placeholder="Phone Number"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
          />

          <div>
            <label className="block text-sm font-medium mb-2">Specialties</label>
            <div className="flex flex-wrap gap-2">
              {specialties.map(specialty => (
                <Badge
                  key={specialty}
                  variant={formData.specialties.includes(specialty) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleSpecialty(specialty)}
                >
                  {specialty.replace('_', ' ')}
                </Badge>
              ))}
            </div>
          </div>

          <Button type="submit" className="w-full">Add Teacher</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dance Studio Manager</h1>
            <p className="text-sm text-gray-600">
              Welcome back, {user.name} ({user.role})
              {user.studio_name && ` - ${user.studio_name}`}
            </p>
          </div>
          <Button variant="outline" onClick={logout}>
            Sign Out
          </Button>
        </div>
      </header>

      <main className="p-6">
        <DashboardStats key={refreshKey} />
        
        <Tabs defaultValue="calendar" className="space-y-6">
          <TabsList>
            <TabsTrigger value="calendar">Schedule</TabsTrigger>
            <TabsTrigger value="classes">Classes</TabsTrigger>
            <TabsTrigger value="teachers">Teachers</TabsTrigger>
          </TabsList>

          <TabsContent value="calendar" className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <CalendarIcon className="h-6 w-6" />
                <h2 className="text-xl font-semibold">Weekly Schedule</h2>
              </div>
              <div className="flex items-center space-x-2">
                <AddClassDialog onClassAdded={handleRefresh} />
                <AddTeacherDialog onTeacherAdded={handleRefresh} />
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-lg">Calendar</CardTitle>
                </CardHeader>
                <CardContent>
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={(date) => date && setSelectedDate(date)}
                    className="rounded-md border"
                  />
                </CardContent>
              </Card>
              
              <div className="lg:col-span-3">
                <WeeklyCalendar 
                  selectedDate={selectedDate} 
                  onDateSelect={setSelectedDate}
                  key={refreshKey}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="classes">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">All Classes</h2>
              {/* Classes list will be implemented here */}
              <p className="text-muted-foreground">Class management coming soon...</p>
            </div>
          </TabsContent>

          <TabsContent value="teachers">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Teachers</h2>
              {/* Teachers list will be implemented here */}
              <p className="text-muted-foreground">Teacher management coming soon...</p>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { token, user } = useAuth();
  const location = useLocation();
  
  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;