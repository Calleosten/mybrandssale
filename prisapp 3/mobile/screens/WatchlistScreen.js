import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  Image,
  StyleSheet,
  Button,
  RefreshControl,
} from "react-native";
import { fetchWatchlist } from "../api";

// I ett riktigt bygge: ersätt med ett stabilt device-ID (t.ex. expo-application)
const DEMO_USER_ID = "demo-user-1";

export default function WatchlistScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWatchlist(DEMO_USER_ID);
      setItems(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <View style={styles.container}>
      <Button
        title="Bläddra bland märken"
        onPress={() => navigation.navigate("ProductList")}
      />

      {error && <Text style={styles.error}>{error}</Text>}

      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListEmptyComponent={
          !loading && (
            <Text style={styles.empty}>
              Du bevakar inga produkter än. Tryck "Bläddra bland märken" för att lägga till.
            </Text>
          )
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            {item.product.image_url && (
              <Image source={{ uri: item.product.image_url }} style={styles.image} />
            )}
            <View style={styles.cardText}>
              <Text style={styles.brand}>{item.product.brand_name}</Text>
              <Text style={styles.name}>{item.product.name}</Text>
              <View style={styles.priceRow}>
                <Text style={styles.price}>{item.product.current_price} kr</Text>
                {item.product.is_on_sale && (
                  <Text style={styles.originalPrice}>{item.product.original_price} kr</Text>
                )}
              </View>
              <Text style={styles.threshold}>
                Notis vid minst {item.notify_threshold_percent}% rabatt
              </Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#fff" },
  error: { color: "red", marginVertical: 8 },
  empty: { marginTop: 24, textAlign: "center", color: "#666" },
  card: {
    flexDirection: "row",
    marginVertical: 8,
    borderWidth: 1,
    borderColor: "#eee",
    borderRadius: 8,
    padding: 8,
  },
  image: { width: 64, height: 64, borderRadius: 6, marginRight: 12 },
  cardText: { flex: 1, justifyContent: "center" },
  brand: { fontSize: 12, color: "#888", textTransform: "uppercase" },
  name: { fontSize: 15, fontWeight: "500" },
  priceRow: { flexDirection: "row", alignItems: "center", marginTop: 4 },
  price: { fontSize: 16, fontWeight: "600", marginRight: 8 },
  originalPrice: { fontSize: 13, color: "#999", textDecorationLine: "line-through" },
  threshold: { fontSize: 11, color: "#aaa", marginTop: 2 },
});
