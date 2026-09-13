import { useEffect, useRef, useState } from "react";
import { Platform } from "react-native";
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { registerDeviceToken } from "../api";

// Visa notisen även om appen är öppen när den kommer in
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/**
 * Begär notis-behörighet, hämtar enhetens FCM-token och registrerar den
 * hos vår backend kopplat till userId.
 *
 * OBS: Detta kräver en "development build" (via `npx expo run:android` /
 * `eas build`) - Expo Go-appen stödjer inte längre push-notiser sedan
 * SDK 49. Se README för instruktioner.
 */
export function usePushNotifications(userId) {
  const [token, setToken] = useState(null);
  const [error, setError] = useState(null);
  const notificationListener = useRef();
  const responseListener = useRef();

  useEffect(() => {
    registerForPushNotifications(userId).then(
      (t) => setToken(t),
      (e) => setError(e.message)
    );

    // Notis mottagen medan appen är öppen
    notificationListener.current = Notifications.addNotificationReceivedListener((notification) => {
      console.log("Notis mottagen:", notification);
    });

    // Användaren tryckte på en notis
    responseListener.current = Notifications.addNotificationResponseReceivedListener((response) => {
      console.log("Notis tryckt:", response);
    });

    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, [userId]);

  return { token, error };
}

async function registerForPushNotifications(userId) {
  if (!Device.isDevice) {
    throw new Error("Push-notiser kräver en fysisk enhet, inte en simulator/emulator.");
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    throw new Error("Notis-behörighet nekades av användaren.");
  }

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  // Native FCM-token (Android) / APNs-token registrerad hos Firebase (iOS)
  const devicePushToken = await Notifications.getDevicePushTokenAsync();
  const fcmToken = devicePushToken.data;

  await registerDeviceToken(userId, fcmToken);

  return fcmToken;
}
