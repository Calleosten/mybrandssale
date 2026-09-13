import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  Image,
  StyleSheet,
  TouchableOpacity,
  Switch,
} from "react-native";
import { fetchProducts, addToWatchlist } from "../api";

const DEMO_USER_ID = "demo-user-1";
const BRANDS = ["Stone Island", "Barena", "Aspesi"];

export default function ProductListScreen() {
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [onSaleOnly, setOnSaleOnly] = useState(true);
  const [products, setProducts] = useState([]);
  const [addedIds, setAddedIds] = useState(new Set());

  const load = useCallback(async () => {
    try {
      const data = await fetchProducts({ brand: selectedBrand, onSaleOnly });
      setProducts(data);
    } catch (e) {
      console.warn(e.message);
    }
  }, [selectedBrand, onSaleOnly]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async (productId) => {
    try {
      await addToWatchlist(DEMO_USER_ID, productId);
      setAddedIds((prev) => new Set(prev).add(productId));
    } catch (e) {
      console.warn(e.message);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.filterRow}>
        {BRANDS.map((b) => (
          <TouchableOpacity
            key={b}
            onPress={() => setSelectedBrand(selectedBrand === b ? null : b)}
            style={[styles.chip, selectedBrand === b && styles.chipActive]}
          >
            <Text style={selectedBrand === b ? styles.chipTextActive : styles.chipText}>
              {b}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.switchRow}>
        <Text>Visa bara rea</Text>
        <Switch value={onSaleOnly} onValueChange={setOnSaleOnly} />
      </View>

      <FlatList
        data={products}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <View style={styles.card}>
            {item.image_url && <Image source={{ uri: item.image_url }} style={styles.image} />}
            <View style={styles.cardText}>
              <Text style={styles.brand}>{item.brand_name}</Text>
              <Text style={styles.name}>{item.name}</Text>
              <Text style={styles.price}>{item.current_price} kr</Text>
            </View>
            <TouchableOpacity
              style={[styles.addButton, addedIds.has(item.id) && styles.addButtonDone]}
              onPress={() => handleAdd(item.id)}
              disabled={addedIds.has(item.id)}
            >
              <Text style={styles.addButtonText}>
                {addedIds.has(item.id) ? "Bevakas" : "Bevaka"}
              </Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#fff" },
  filterRow: { flexDirection: "row", flexWrap: "wrap", marginBottom: 8 },
  chip: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 12,
    marginRight: 8,
    marginBottom: 8,
  },
  chipActive: { backgroundColor: "#222", borderColor: "#222" },
  chipText: { color: "#333" },
  chipTextActive: { color: "#fff" },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 6,
    borderWidth: 1,
    borderColor: "#eee",
    borderRadius: 8,
    padding: 8,
  },
  image: { width: 56, height: 56, borderRadius: 6, marginRight: 12 },
  cardText: { flex: 1 },
  brand: { fontSize: 12, color: "#888", textTransform: "uppercase" },
  name: { fontSize: 14, fontWeight: "500" },
  price: { fontSize: 14, marginTop: 2 },
  addButton: {
    backgroundColor: "#222",
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  addButtonDone: { backgroundColor: "#999" },
  addButtonText: { color: "#fff", fontSize: 12 },
});
