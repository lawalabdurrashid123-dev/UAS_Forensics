import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

// Import your screens - ensure these file names match your actual files in the /screens folder
import MedicineList from './screens/MedicineList';
import HistoryScreen from './screens/HistoryScreen';
import ExpiryScreen from './screens/ExpiryScreen';
import TransactionScreen from './screens/TransactionScreen';
import AddMedicineScreen from './screens/AddMedicineScreen';

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Stock">
        <Stack.Screen name="Stock" component={MedicineList} />
        <Stack.Screen name="History" component={HistoryScreen} />
        <Stack.Screen name="Expiry" component={ExpiryScreen} />
        <Stack.Screen name="Transaction" component={TransactionScreen} />
        <Stack.Screen name="AddMedicine" component={AddMedicineScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}