import React from "react";
import { Text } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import ProductListScreen from "./screens/ProductListScreen";
import WatchlistScreen from "./screens/WatchlistScreen";
import { usePushNotifications } from "./hooks/usePushNotifications";

const Stack = createNativeStackNavigator();

// Samma demo-ID som används i screens/ - byt ut mot ett stabilt device-ID
// eller inloggat användar-ID i en riktig app.
const DEMO_USER_ID = "demo-user-1";

export default function App() {
  const { error: pushError } = usePushNotifications(DEMO_USER_ID);

  return (
    <NavigationContainer>
      {pushError && (
        <Text style={{ padding: 8, fontSize: 12, color: "#999", textAlign: "center" }}>
          Notiser avstängda: {pushError}
        </Text>
      )}
      <Stack.Navigator initialRouteName="Watchlist">
        <Stack.Screen
          name="Watchlist"
          component={WatchlistScreen}
          options={{ title: "Din bevakningslista" }}
        />
        <Stack.Screen
          name="ProductList"
          component={ProductListScreen}
          options={{ title: "Bläddra & lägg till" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
